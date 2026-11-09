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
COMPONENT_FILES = {
    "svelte-dist/index.js",
    "svelte-dist/index.d.ts",
    "svelte-dist/types.js",
    "svelte-dist/types.d.ts",
    "svelte-dist/AccountMenu.svelte",
    "svelte-dist/AccountMenu.svelte.d.ts",
    "svelte-dist/LegalLinks.svelte",
    "svelte-dist/LegalLinks.svelte.d.ts",
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
    expected = {"package.json", "README.md", "LICENSE", f"{STATIC}/design.css"} | COMPONENT_FILES
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
    assert set(exports) == {".", "./design.css"}
    assert set(exports["."]) == {"types", "svelte"}
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


def test_a_consumer_imports_legal_links_and_its_props_type_from_the_package_root(tarball, tmp_path):
    name = json.loads((tarball / "package.json").read_text())["name"]
    modules = tmp_path / "node_modules"
    modules.mkdir()
    shutil.copytree(tarball, modules / name)
    (modules / "svelte").symlink_to(REPOSITORY / "node_modules/svelte")
    (tmp_path / "consumer.ts").write_text(
        f"import {{ LegalLinks, type LegalLinksProps }} from '{name}';\n"
        "const props: LegalLinksProps = { links: [{ label: 'Imprint', href: '/imprint' }] };\n"
        "export const component: typeof LegalLinks = LegalLinks;\n"
        "// @ts-expect-error links is required\n"
        "export const missing: LegalLinksProps = {};\n"
        "export { props };\n"
        "export const menuPlace: LegalLinksProps = { links: [], place: 'menu' };\n"
        "export const pageNewTab: LegalLinksProps = { links: [], place: 'page', newTab: true };\n"
        "export const defaultPlaceNewTab: LegalLinksProps = { links: [], newTab: true };\n"
        "// @ts-expect-error the menu place always opens a new tab\n"
        "export const menuNewTab: LegalLinksProps = { links: [], place: 'menu', newTab: true };\n"
    )
    result = subprocess.run(
        [
            str(REPOSITORY / "node_modules/.bin/tsc"),
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
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout


def test_a_consumer_gives_the_no_access_state_at_most_one_log_out_form_and_a_released_state_still_type_checks(
    tarball, tmp_path
):
    name = json.loads((tarball / "package.json").read_text())["name"]
    modules = tmp_path / "node_modules"
    modules.mkdir()
    shutil.copytree(tarball, modules / name)
    (modules / "svelte").symlink_to(REPOSITORY / "node_modules/svelte")
    (tmp_path / "consumer.ts").write_text(
        f"import type {{ LogOut, SignInState }} from '{name}';\n"
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
    result = subprocess.run(
        [str(REPOSITORY / "node_modules/.bin/tsc"), *TSC_ARGUMENTS],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout


def test_a_consumer_gives_each_sign_in_state_only_its_own_props(tarball, tmp_path):
    name = json.loads((tarball / "package.json").read_text())["name"]
    modules = tmp_path / "node_modules"
    modules.mkdir()
    shutil.copytree(tarball, modules / name)
    (modules / "svelte").symlink_to(REPOSITORY / "node_modules/svelte")
    (tmp_path / "consumer.ts").write_text(
        f"import type {{ SignInPageProps }} from '{name}';\n"
        "export const starting: SignInPageProps = {\n"
        "  appName: 'A', state: { page: 'signed-out', signInHref: '/in', onSignIn: () => {}, unfinished: true },\n"
        "  legalLinks: [],\n"
        "};\n"
        "export const waiting: SignInPageProps = {\n"
        "  appName: 'A', state: { page: 'signing-in', tabHref: '/t' }, legalLinks: [],\n"
        "};\n"
        "export const waitingWithoutLink: SignInPageProps = {\n"
        "  appName: 'A',\n"
        "  // @ts-expect-error signing-in needs tabHref\n"
        "  state: { page: 'signing-in' },\n"
        "  legalLinks: [],\n"
        "};\n"
        "export const waitingWithSignInHref: SignInPageProps = {\n"
        "  appName: 'A',\n"
        "  // @ts-expect-error signing-in refuses signInHref\n"
        "  state: { page: 'signing-in', tabHref: '/t', signInHref: '/in' },\n"
        "  legalLinks: [],\n"
        "};\n"
        "export const failedWithHandler: SignInPageProps = {\n"
        "  appName: 'A',\n"
        "  // @ts-expect-error onSignIn exists only on signed-out\n"
        "  state: { page: 'login-failed', signInHref: '/in', onSignIn: () => {} },\n"
        "  legalLinks: [],\n"
        "};\n"
        "export const failedUnfinished: SignInPageProps = {\n"
        "  appName: 'A',\n"
        "  // @ts-expect-error unfinished exists only on signed-out\n"
        "  state: { page: 'login-failed', signInHref: '/in', unfinished: true },\n"
        "  legalLinks: [],\n"
        "};\n"
    )
    result = subprocess.run(
        [str(REPOSITORY / "node_modules/.bin/tsc"), *TSC_ARGUMENTS],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout


def test_a_consumer_gives_the_account_menu_one_log_out_form_and_a_typed_theme_choice(tarball, tmp_path):
    name = json.loads((tarball / "package.json").read_text())["name"]
    modules = tmp_path / "node_modules"
    modules.mkdir()
    shutil.copytree(tarball, modules / name)
    (modules / "svelte").symlink_to(REPOSITORY / "node_modules/svelte")
    (tmp_path / "consumer.ts").write_text(
        f"import {{ AccountMenu, type AccountMenuProps, type ThemeChoice }} from '{name}';\n"
        "const common = { name: 'F', accountHref: '/a', onAccountOpen: () => {}, appRows: [], legalLinks: [] };\n"
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
    result = subprocess.run(
        [str(REPOSITORY / "node_modules/.bin/tsc"), *TSC_ARGUMENTS],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout


def test_a_consumer_imports_both_words_types_from_the_package_root_and_gives_each_whole(tarball, tmp_path):
    name = json.loads((tarball / "package.json").read_text())["name"]
    modules = tmp_path / "node_modules"
    modules.mkdir()
    shutil.copytree(tarball, modules / name)
    (modules / "svelte").symlink_to(REPOSITORY / "node_modules/svelte")
    (tmp_path / "consumer.ts").write_text(
        f"import type {{ AccountMenuProps, AccountMenuWords, SignInPageProps, SignInPageWords }} from '{name}';\n"
        "const menuWords: AccountMenuWords = { theme: 'T', followSystem: 'F', light: 'L', dark: 'D', logOut: 'O' };\n"
        "const pageWords: SignInPageWords = {\n"
        "  loggedOut: 'a', logIn: 'b', loginFailed: 'c', loginFailedBanner: 'd',\n"
        "  tryAgain: 'e', noAccess: 'f', noAccessSentence: (appName: string) => appName, logOut: 'g',\n"
        "  signingIn: 'h', inOtherWindow: 'i', openInTab: 'j', signInUnfinished: 'k',\n"
        "};\n"
        "export const menu: AccountMenuProps = {\n"
        "  name: 'F', accountHref: '/a', onAccountOpen: () => {}, appRows: [], legalLinks: [],\n"
        "  logOutAction: '/l', words: menuWords,\n"
        "};\n"
        "export const page: SignInPageProps = {\n"
        "  appName: 'A', state: { page: 'signed-out', signInHref: '/in' }, legalLinks: [], words: pageWords,\n"
        "};\n"
        "type OptionalKeys<T> = { [K in keyof T]-?: {} extends Pick<T, K> ? K : never }[keyof T];\n"
        "export const menuHasNoOptionalWord: [OptionalKeys<AccountMenuWords>] extends [never] ? true : false = true;\n"
        "export const pageHasNoOptionalWord: [OptionalKeys<SignInPageWords>] extends [never] ? true : false = true;\n"
        "// @ts-expect-error a record of menu words is whole\n"
        "export const partialMenu: AccountMenuWords = { theme: 'T' };\n"
        "// @ts-expect-error a record of page words is whole\n"
        "export const partialPage: SignInPageWords = { logIn: 'b' };\n"
        "// @ts-expect-error the no-access sentence is a function of the app name\n"
        "export const textSentence: SignInPageWords = { ...pageWords, noAccessSentence: 'f' };\n"
    )
    result = subprocess.run(
        [str(REPOSITORY / "node_modules/.bin/tsc"), *TSC_ARGUMENTS],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout
