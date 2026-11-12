import json
import re
import shutil
import subprocess
import tarfile
import tomllib
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parent.parent
STATIC = "src/design/static"
INSTALL_SCRIPTS = {"preinstall", "install", "postinstall", "prepare"}
STORAGE_AND_NETWORK = (
    "localStorage",
    "sessionStorage",
    "indexedDB",
    "document.cookie",
    "fetch",
    "XMLHttpRequest",
    "sendBeacon",
    "WebSocket",
    "dataset.theme",
)
TSC_ARGUMENTS = [
    "--noEmit",
    "--strict",
    "--skipLibCheck",
    "--module",
    "esnext",
    "--moduleResolution",
    "bundler",
    "--target",
    "es2022",
    "--allowImportingTsExtensions",
    "--verbatimModuleSyntax",
    "consumer.ts",
]
SVELTE_TSCONFIG = json.dumps(
    {
        "compilerOptions": {
            "strict": True,
            "skipLibCheck": True,
            "noEmit": True,
            "module": "esnext",
            "moduleResolution": "bundler",
            "target": "es2022",
            "verbatimModuleSyntax": True,
            "allowImportingTsExtensions": True,
        },
        "include": ["*.svelte", "*.ts"],
    }
)
TSC_WITHOUT_TS_ENDINGS = [argument for argument in TSC_ARGUMENTS if argument != "--allowImportingTsExtensions"]
COMPONENT_FILES = {
    "svelte-dist/index.js",
    "svelte-dist/index.d.ts",
    "svelte-dist/kitWords.js",
    "svelte-dist/kitWords.d.ts",
    "svelte-dist/types.js",
    "svelte-dist/types.d.ts",
    "svelte-dist/AccountMenu.svelte",
    "svelte-dist/AccountMenu.svelte.d.ts",
    "svelte-dist/AgentControl.svelte",
    "svelte-dist/AgentControl.svelte.d.ts",
    "svelte-dist/AiMark.svelte",
    "svelte-dist/AiMark.svelte.d.ts",
    "svelte-dist/LegalLinks.svelte",
    "svelte-dist/LegalLinks.svelte.d.ts",
    "svelte-dist/Marked.svelte",
    "svelte-dist/Marked.svelte.d.ts",
    "svelte-dist/SignInPage.svelte",
    "svelte-dist/SignInPage.svelte.d.ts",
}


@pytest.fixture(scope="module")
def tarball(tmp_path_factory):
    """The package as a consumer gets it: packed by pnpm, read back from the tarball."""
    root = tmp_path_factory.mktemp("npm")
    subprocess.run(
        ["pnpm", "pack", "--pack-destination", str(root)],
        cwd=REPOSITORY,
        check=True,
        capture_output=True,
    )
    (archive,) = root.glob("*.tgz")
    unpacked = root / "unpacked"
    with tarfile.open(archive) as opened:
        opened.extractall(unpacked, filter="data")
    return unpacked / "package"


class Consumer:
    """A project that installed the packed package, type-checked the way an app's compiler sees it."""

    def __init__(self, name, project):
        self.name = name
        self.project = project

    def check(self, source, arguments=TSC_ARGUMENTS):
        (self.project / "consumer.ts").write_text(source)
        result = subprocess.run(
            [str(REPOSITORY / "node_modules/.bin/tsc"), *arguments],
            cwd=self.project,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout

    def run_node(self, source, *arguments):
        """Runs an ES module source in a plain Node process of the project; returns its output."""
        result = subprocess.run(
            ["node", "--input-type=module", "--eval", source, *arguments],
            cwd=self.project,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
        return result.stdout

    def check_page(self, source):
        """Type-check a Svelte page the way an app's svelte-check sees it; returns the exit status and the findings."""
        (self.project / "tsconfig.json").write_text(SVELTE_TSCONFIG)
        (self.project / "Page.svelte").write_text(source)
        result = subprocess.run(
            [
                str(REPOSITORY / "node_modules/.bin/svelte-check"),
                "--workspace",
                str(self.project),
                "--tsconfig",
                "tsconfig.json",
                "--output",
                "machine",
            ],
            cwd=self.project,
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stdout


@pytest.fixture
def consumer(tarball, tmp_path):
    name = json.loads((tarball / "package.json").read_text())["name"]
    modules = tmp_path / "node_modules"
    modules.mkdir()
    shutil.copytree(tarball, modules / name)
    (modules / "svelte").symlink_to(REPOSITORY / "node_modules/svelte")
    return Consumer(name, tmp_path)


def catalog_languages():
    return sorted(path.stem for path in (REPOSITORY / "src" / "catalogs").glob("*.po"))


def kit_words_files():
    """The generated words: the loader and one module with its declaration per catalog."""
    return {
        f"svelte-dist/words/{stem}{ending}" for stem in ["index", *catalog_languages()] for ending in (".js", ".d.ts")
    }


def packed_files(package):
    return {path.relative_to(package).as_posix() for path in package.rglob("*") if path.is_file()}


def export_targets(exports):
    """Every file an exports map names, through nested conditions."""
    if isinstance(exports, str):
        return {exports}
    return set().union(*(export_targets(value) for value in exports.values()))


def test_tarball_holds_exactly_the_manifest_readme_licence_stylesheet_fonts_font_licences_and_component(
    tarball, font_files, licences
):
    expected = {"package.json", "README.md", "LICENSE", f"{STATIC}/design.css"} | COMPONENT_FILES | kit_words_files()
    expected |= {f"{STATIC}/fonts/{name}" for name in font_files | licences}
    assert packed_files(tarball) == expected


def test_every_export_target_is_a_packed_file(tarball):
    exports = json.loads((tarball / "package.json").read_text())["exports"]
    assert exports
    for target in export_targets(exports):
        assert (tarball / target).is_file(), target


def test_every_url_in_the_packed_stylesheet_names_a_packed_font(tarball, font_files, stylesheet_urls):
    stylesheet = tarball / STATIC / "design.css"
    urls = stylesheet_urls(stylesheet)
    assert len(urls) == len(font_files)
    for url in urls:
        assert (stylesheet.parent / url).is_file(), url


def test_packed_stylesheet_is_byte_equal_to_the_source_stylesheet(tarball):
    source = REPOSITORY / STATIC / "design.css"
    assert (tarball / STATIC / "design.css").read_bytes() == source.read_bytes()


def test_manifest_is_private_and_exports_the_component_with_types_and_the_stylesheet_as_design_css(tarball):
    manifest = json.loads((tarball / "package.json").read_text())
    assert manifest["private"] is True
    exports = manifest["exports"]
    assert set(exports) == {".", "./design.css", "./words"}
    assert set(exports["."]) == {"types", "svelte"}
    assert list(exports["./words"]) == ["types", "default"]
    assert exports["./design.css"] == f"./{STATIC}/design.css"


def test_package_version_equals_the_python_package_version(tarball):
    python_version = tomllib.loads((REPOSITORY / "pyproject.toml").read_text())["project"]["version"]
    assert json.loads((tarball / "package.json").read_text())["version"] == python_version


def test_package_has_only_svelte_as_a_peer_and_no_install_scripts(tarball):
    manifest = json.loads((tarball / "package.json").read_text())
    assert not {"dependencies", "optionalDependencies"} & manifest.keys()
    assert manifest["peerDependencies"].keys() == {"svelte"}
    assert not INSTALL_SCRIPTS & manifest.get("scripts", {}).keys()


def test_shipped_components_use_no_light_dark_inline_style_or_style_directives_a_linked_stylesheet_cannot_serve(
    tarball,
):
    components = sorted((tarball / "svelte-dist").glob("*.svelte"))
    assert components
    for component in components:
        source = component.read_text()
        assert "light-dark(" not in source, component.name
        assert "style=" not in source, component.name
        assert "style:" not in source, component.name


def test_shipped_components_neither_store_nor_fetch_nor_write_the_theme_which_the_app_owns(tarball):
    for component in sorted((tarball / "svelte-dist").glob("*.svelte")):
        source = component.read_text()
        for forbidden in STORAGE_AND_NETWORK:
            assert forbidden not in source, (component.name, forbidden)
        assert not re.search(r"setAttribute\([^)]*data-theme", source), component.name


def test_a_consumer_imports_legal_links_and_its_props_type_from_the_package_root(consumer):
    consumer.check(
        f"import {{ LegalLinks, type KitWords, type LegalLinksProps }} from '{consumer.name}';\n"
        "declare const words: KitWords;\n"
        "const props: LegalLinksProps = { links: [{ label: 'Imprint', href: '/imprint' }], words };\n"
        "export const component: typeof LegalLinks = LegalLinks;\n"
        "// @ts-expect-error links is required\n"
        "export const missing: LegalLinksProps = {};\n"
        "export { props };\n"
        "export const menuPlace: LegalLinksProps = { links: [], words, place: 'menu' };\n"
        "export const pageNewTab: LegalLinksProps = { links: [], words, place: 'page', newTab: true };\n"
        "export const defaultPlaceNewTab: LegalLinksProps = { links: [], words, newTab: true };\n"
        "// @ts-expect-error the menu place always opens a new tab\n"
        "export const menuNewTab: LegalLinksProps = { links: [], words, place: 'menu', newTab: true };\n"
    )


def test_a_consumer_gives_the_no_access_state_at_most_one_log_out_form_and_a_released_state_still_type_checks(
    consumer,
):
    consumer.check(
        f"import type {{ LogOut, SignInState }} from '{consumer.name}';\n"
        "export const callback: SignInState = { page: 'no-access', onLogOut: () => {}, logOutFailure: 'x' };\n"
        "export const action: SignInState = { page: 'no-access', logOutAction: '/logout' };\n"
        "export const shared: LogOut = { logOutAction: '/logout' };\n"
        "export const none: SignInState = { page: 'no-access' };\n"
        "// @ts-expect-error a failure text needs the callback form\n"
        "export const failureWithoutForm: SignInState = { page: 'no-access', logOutFailure: 'x' };\n"
        "// @ts-expect-error both forms\n"
        "export const both: SignInState = { page: 'no-access', onLogOut: () => {}, logOutAction: '/logout' };\n"
        "// @ts-expect-error a failure text belongs to the callback form\n"
        "export const mixed: SignInState = { page: 'no-access', logOutAction: '/logout', logOutFailure: 'x' };\n"
    )


def test_a_consumer_gives_each_sign_in_state_only_its_own_props(consumer):
    consumer.check(
        f"import type {{ KitWords, SignInPageProps }} from '{consumer.name}';\n"
        "declare const words: KitWords;\n"
        "export const starting: SignInPageProps = {\n"
        "  appName: 'A', state: { page: 'signed-out', signInHref: '/in', onSignIn: () => {}, unfinished: true },\n"
        "  legalLinks: [], words,\n"
        "};\n"
        "export const waiting: SignInPageProps = {\n"
        "  appName: 'A', state: { page: 'signing-in', tabHref: '/t' }, legalLinks: [], words,\n"
        "};\n"
        "export const waitingWithoutLink: SignInPageProps = {\n"
        "  appName: 'A',\n"
        "  // @ts-expect-error signing-in needs tabHref\n"
        "  state: { page: 'signing-in' },\n"
        "  legalLinks: [], words,\n"
        "};\n"
        "export const waitingWithSignInHref: SignInPageProps = {\n"
        "  appName: 'A',\n"
        "  // @ts-expect-error signing-in refuses signInHref\n"
        "  state: { page: 'signing-in', tabHref: '/t', signInHref: '/in' },\n"
        "  legalLinks: [], words,\n"
        "};\n"
        "const frame = { appName: 'A', legalLinks: [], words };\n"
        "export const blocked: SignInPageProps = { ...frame, state: { page: 'window-blocked', tabHref: '/t' } };\n"
        "// @ts-expect-error window-blocked needs tabHref\n"
        "export const blockedWithoutLink: SignInPageProps = { ...frame, state: { page: 'window-blocked' } };\n"
        "export const blockedWithSignInHref: SignInPageProps = {\n"
        "  // @ts-expect-error window-blocked refuses signInHref\n"
        "  ...frame, state: { page: 'window-blocked', tabHref: '/t', signInHref: '/in' },\n"
        "};\n"
        "export const failedWithHandler: SignInPageProps = {\n"
        "  appName: 'A',\n"
        "  // @ts-expect-error onSignIn exists only on signed-out\n"
        "  state: { page: 'login-failed', signInHref: '/in', onSignIn: () => {} },\n"
        "  legalLinks: [], words,\n"
        "};\n"
        "export const failedUnfinished: SignInPageProps = {\n"
        "  appName: 'A',\n"
        "  // @ts-expect-error unfinished exists only on signed-out\n"
        "  state: { page: 'login-failed', signInHref: '/in', unfinished: true },\n"
        "  legalLinks: [], words,\n"
        "};\n"
    )


def test_a_consumer_gives_the_account_menu_one_log_out_form_and_a_typed_theme_choice(consumer):
    consumer.check(
        f"import {{ AccountMenu, type AccountMenuProps, type KitWords, type ThemeChoice }} from '{consumer.name}';\n"
        "declare const words: KitWords;\n"
        "const common = {\n"
        "  name: 'F', accountHref: '/a', onAccountOpen: () => {}, appRows: [], legalLinks: [], words,\n"
        "};\n"
        "export const component: typeof AccountMenu = AccountMenu;\n"
        "export const callback: AccountMenuProps = { ...common, onLogOut: () => {}, logOutFailure: 'x' };\n"
        "export const action: AccountMenuProps = { ...common, logOutAction: '/logout' };\n"
        "export const choice: ThemeChoice = 'follow-system';\n"
        "export const themed: AccountMenuProps = { ...common, logOutAction: '/l', "
        "theme: { choice: 'dark', onChange: (next: ThemeChoice) => void next } };\n"
        "export const row: AccountMenuProps = { ...common, logOutAction: '/l', "
        "appRows: [{ label: 'S', onSelect: () => {} }] };\n"
        "// @ts-expect-error a choice outside the union\n"
        "export const wrong: AccountMenuProps = { ...common, logOutAction: '/l', "
        "theme: { choice: 'sepia', onChange: () => {} } };\n"
        "// @ts-expect-error a choice without its callback\n"
        "export const silent: AccountMenuProps = { ...common, logOutAction: '/l', theme: { choice: 'dark' } };\n"
        "// @ts-expect-error an app row that still carries icon\n"
        "export const rowWithIcon: AccountMenuProps = { ...common, logOutAction: '/l', "
        "appRows: [{ label: 'S', icon: 'settings', onSelect: () => {} }] };\n"
        "// @ts-expect-error neither log-out form\n"
        "export const neither: AccountMenuProps = { ...common };\n"
        "// @ts-expect-error both log-out forms\n"
        "export const both: AccountMenuProps = { ...common, onLogOut: () => {}, logOutAction: '/l' };\n"
        "// @ts-expect-error a failure text belongs to the callback form\n"
        "export const mixed: AccountMenuProps = { ...common, logOutAction: '/l', logOutFailure: 'x' };\n"
    )


COMPONENT_PROPS = {
    "AccountMenu": (
        "{ name: 'F', accountHref: '/a', onAccountOpen: () => {}, appRows: [], legalLinks: [], logOutAction: '/l'"
    ),
    "SignInPage": "{ appName: 'A', state: { page: 'signed-out', signInHref: '/in' }, legalLinks: []",
    "AgentControl": "{ rows: [], onCall: (key: string) => void key",
    "LegalLinks": "{ links: []",
}


@pytest.mark.parametrize("component", COMPONENT_PROPS)
def test_a_consumer_passes_the_kit_words_to_each_component_and_fails_its_type_check_without_them(consumer, component):
    props = COMPONENT_PROPS[component]
    consumer.check(
        f"import {{ {component}, type KitWords }} from '{consumer.name}';\n"
        "import type { ComponentProps } from 'svelte';\n"
        f"type Props = ComponentProps<typeof {component}>;\n"
        "declare const words: KitWords;\n"
        f"export const worded: Props = {props}, words }};\n"
        f"export const overridden: Props = {props}, words: {{ ...words, 'account.logOut': 'Exit' }} }};\n"
        "// @ts-expect-error the words are required\n"
        f"export const unworded: Props = {props} }};\n"
        "// @ts-expect-error the words are not optional\n"
        f"export const undefinedWords: Props = {props}, words: undefined }};\n"
    )


@pytest.mark.parametrize("removed", ["AccountMenuWords", "SignInPageWords", "AgentControlWords"])
def test_the_package_root_exports_no_per_component_words_type(consumer, removed):
    consumer.check(
        f"// @ts-expect-error the package exports no such type\nimport type {{ {removed} }} from '{consumer.name}';\n"
    )


def test_a_consumer_imports_the_kit_words_loader_and_both_types_from_the_package_root(consumer):
    consumer.check(
        f"import {{ loadKitWords, type KitLanguage, type KitWords }} from '{consumer.name}';\n"
        "export const loaded: (language: KitLanguage) => Promise<KitWords> = loadKitWords;\n"
    )


def test_a_consumer_imports_the_kit_words_from_the_words_export_without_allowing_ts_import_endings(consumer):
    consumer.check(
        f"import {{ loadKitWords, type KitLanguage, type KitWords }} from '{consumer.name}/words';\n"
        "export const loaded: (language: KitLanguage) => Promise<KitWords> = loadKitWords;\n",
        TSC_WITHOUT_TS_ENDINGS,
    )


def test_a_plain_node_process_loads_the_words_of_every_kit_language_from_the_words_export(consumer):
    catalogs = REPOSITORY / "src" / "catalogs"
    first_key = re.search(r'^msgctxt "(.+)"$', (catalogs / "de.po").read_text(), re.MULTILINE).group(1)
    output = consumer.run_node(
        f"import {{ loadKitWords }} from '{consumer.name}/words';"
        "const keys = {};"
        "for (const language of process.argv.slice(1)) keys[language] = Object.keys(await loadKitWords(language));"
        "process.stdout.write(JSON.stringify(keys));",
        *catalog_languages(),
    )
    keys = json.loads(output)
    assert sorted(keys) == catalog_languages()
    for language, loaded in keys.items():
        assert first_key in loaded, language


def test_a_consumer_cannot_load_kit_words_for_a_language_the_kit_lacks(consumer):
    consumer.check(
        f"import {{ loadKitWords }} from '{consumer.name}';\n"
        "// @ts-expect-error the kit ships no pl words\n"
        "export const polish = loadKitWords('pl');\n"
    )


def test_a_consumer_list_of_the_kit_languages_satisfies_kit_language_and_one_with_a_missing_language_does_not(consumer):
    covered = ", ".join(f"'{language}'" for language in catalog_languages())
    consumer.check(
        f"import type {{ KitLanguage }} from '{consumer.name}';\n"
        f"export const covered = [{covered}] as const satisfies readonly KitLanguage[];\n"
        "// @ts-expect-error the kit lacks pl\n"
        "export const lacking = ['de', 'pl'] as const satisfies readonly KitLanguage[];\n"
    )


def test_a_consumer_imports_the_ai_mark_from_the_package_root(consumer):
    consumer.check(f"import {{ AiMark }} from '{consumer.name}';\nexport const component: typeof AiMark = AiMark;\n")


def test_a_consumer_imports_the_agent_control_with_its_types_from_the_package_root(
    consumer,
):
    consumer.check(
        f"import {{ AgentControl, type AgentControlProps, type AgentControlRefusal, type AgentRow, "
        f"type KitWords }} from '{consumer.name}';\n"
        "export const component: typeof AgentControl = AgentControl;\n"
        "declare const words: KitWords;\n"
        "const common = { onCall: (key: string) => void key, onSendAway: (key: string) => void key, words };\n"
        "const rows: AgentRow[] = [\n"
        "  { key: 'k1', name: 'Mozart', state: 'available' },\n"
        "  { key: 'k2', name: 'Bach', state: 'inviting' },\n"
        "  { key: 'k3', name: 'Leonardo', state: 'here' },\n"
        "];\n"
        "export const plain: AgentControlProps = { ...common, rows };\n"
        "export const withoutSendAway: AgentControlProps = { onCall: (key: string) => void key, rows, words };\n"
        "export const refused: AgentControlProps = { ...common, rows, refusal: 'place-full' };\n"
        "export const reasons: AgentControlRefusal[] = [\n"
        "  'not-allowed', 'owner-absent', 'place-full', 'agent-unavailable', 'try-again',\n"
        "];\n"
        "// @ts-expect-error a refusal outside the five reasons\n"
        "export const unknownRefusal: AgentControlProps = { ...common, rows, refusal: 'sorry' };\n"
        "// @ts-expect-error a state outside the three\n"
        "export const unknownState: AgentRow = { key: 'k', name: 'N', state: 'gone' };\n"
        "// @ts-expect-error the rows are required\n"
        "export const noRows: AgentControlProps = { ...common };\n"
    )


MARKED_PAGE = """<script lang="ts">
  import { Marked } from '%s';
  const note: readonly (string | { readonly marker: "strong" | "link"; readonly text: string })[] = [];
  const snippets = { strong, link, code };
</script>
{#snippet strong(text: string)}<strong>{text}</strong>{/snippet}
{#snippet link(text: string)}<a href="/more">{text}</a>{/snippet}
{#snippet code(text: string)}<code>{text}</code>{/snippet}
%s
"""


def test_a_consumer_page_renders_a_marked_sentence_and_an_unused_snippet_in_a_variable_is_harmless(
    consumer,
):
    status, findings = consumer.check_page(
        MARKED_PAGE
        % (
            consumer.name,
            "<Marked parts={note} marked={{ strong, link }} />\n<Marked parts={note} marked={snippets} />",
        )
    )
    assert status == 0, findings


@pytest.mark.parametrize(
    ("markup", "finding"),
    [
        pytest.param(
            "<Marked parts={note} marked={{ strong }} />", "Property 'link' is missing", id="a missing snippet"
        ),
        pytest.param("<Marked parts={note} marked={{}} />", "is missing the following properties", id="no snippets"),
        pytest.param(
            "<Marked parts={note} marked={{ strong, link, code }} />",
            "'code' does not exist",
            id="a snippet for a marker the sentence lacks",
        ),
        pytest.param("<Marked marked={{ strong, link }} />", "Property 'parts' is missing", id="no parts"),
    ],
)
def test_a_consumer_page_with_a_missing_or_an_unused_snippet_in_place_fails_its_type_check(consumer, markup, finding):
    status, findings = consumer.check_page(MARKED_PAGE % (consumer.name, markup))
    assert status != 0
    assert "Page.svelte" in findings
    assert finding in findings
