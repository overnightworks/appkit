import functools
import http.server
import json
import re
import shutil
import subprocess
import tarfile
import threading
import tomllib
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parent.parent
STATIC = "src/appkit/static"
INSTALL_SCRIPTS = {"preinstall", "install", "postinstall", "prepare"}
COMPONENT_FILES = {
    "svelte-dist/index.js",
    "svelte-dist/index.d.ts",
    "svelte-dist/types.js",
    "svelte-dist/types.d.ts",
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


def test_tarball_holds_exactly_the_manifest_readme_licence_stylesheet_fonts_font_licences_and_component(tarball, font_files, licences):
    expected = {"package.json", "README.md", "LICENSE", f"{STATIC}/appkit.css"} | COMPONENT_FILES
    expected |= {f"{STATIC}/fonts/{name}" for name in font_files | licences}
    assert packed_files(tarball) == expected


def test_every_export_target_is_a_packed_file(tarball):
    exports = json.loads((tarball / "package.json").read_text())["exports"]
    assert exports
    for target in export_targets(exports):
        assert (tarball / target).is_file(), target


def test_every_url_in_the_packed_stylesheet_names_a_packed_font(tarball, font_files, stylesheet_urls):
    stylesheet = tarball / STATIC / "appkit.css"
    urls = stylesheet_urls(stylesheet)
    assert len(urls) == len(font_files)
    for url in urls:
        assert (stylesheet.parent / url).is_file(), url


def test_packed_stylesheet_is_byte_equal_to_the_source_stylesheet(tarball):
    source = REPOSITORY / STATIC / "appkit.css"
    assert (tarball / STATIC / "appkit.css").read_bytes() == source.read_bytes()


def test_manifest_is_private_and_exports_the_component_with_types_and_the_stylesheet_as_appkit_css(tarball):
    manifest = json.loads((tarball / "package.json").read_text())
    assert manifest["private"] is True
    exports = manifest["exports"]
    assert set(exports) == {".", "./appkit.css"}
    assert set(exports["."]) == {"types", "svelte"}
    assert exports["./appkit.css"] == f"./{STATIC}/appkit.css"


def test_package_version_equals_the_python_package_version(tarball):
    python_version = tomllib.loads((REPOSITORY / "pyproject.toml").read_text())["project"]["version"]
    assert json.loads((tarball / "package.json").read_text())["version"] == python_version


def test_package_has_only_svelte_as_a_peer_and_no_install_scripts(tarball):
    manifest = json.loads((tarball / "package.json").read_text())
    assert not {"dependencies", "optionalDependencies"} & manifest.keys()
    assert manifest["peerDependencies"].keys() == {"svelte"}
    assert not INSTALL_SCRIPTS & manifest.get("scripts", {}).keys()


GLOW_ALPHA_BY_THEME = {"light": 0.04, "dark": 0.03}
CONSUMER_ENTRY = """\
import {{ mount }} from 'svelte';
import {{ SignInPage }} from 'overnightworks-appkit';
{stylesheet_import}
document.documentElement.dataset.theme = location.hash.slice(1);
mount(SignInPage, {{
  target: document.body,
  props: {{ appName: 'App', state: {{ page: 'signed-out', signInHref: '/in' }}, legalLinks: [] }}
}});
setTimeout(() => {{
  document.title = getComputedStyle(document.querySelector('.grid-bg')).backgroundImage;
}}, 300);
"""
CONSUMER_PAGE = "<!doctype html><html><head>{stylesheet_link}<link rel=stylesheet href=/app.css></head><body><script type=module src=/main.js></script></body></html>"
CONSUMER_COLOURS = ":root { --primary: #7c3aed; --accent: #f59e0b; }"
CONSUMER_VITE_CONFIG = (
    "import { svelte } from '@sveltejs/vite-plugin-svelte';\n"
    "export default { plugins: [svelte()], build: { modulePreload: false } };\n"
)


def build_consumer(package, root, stylesheet_linked):
    """A production-built app that uses the packed component, with appkit.css linked as a file or bundled by the build."""
    modules = root / "node_modules"
    (modules / "@sveltejs").mkdir(parents=True)
    for name in ("svelte", "vite", "@sveltejs/vite-plugin-svelte"):
        (modules / name).symlink_to((REPOSITORY / "node_modules" / name).resolve())
    shutil.copytree(package, modules / "overnightworks-appkit")
    (root / "public").mkdir()
    (root / "public/app.css").write_text(CONSUMER_COLOURS)
    stylesheet = package / STATIC / "appkit.css"
    shutil.copytree(stylesheet.parent, root / "public/static")
    (root / "index.html").write_text(
        CONSUMER_PAGE.format(stylesheet_link="<link rel=stylesheet href=/static/appkit.css>" if stylesheet_linked else "")
    )
    (root / "main.js").write_text(
        CONSUMER_ENTRY.format(stylesheet_import="" if stylesheet_linked else "import 'overnightworks-appkit/appkit.css';")
    )
    (root / "vite.config.mjs").write_text(CONSUMER_VITE_CONFIG)
    subprocess.run(
        ["node", str(modules / "vite/bin/vite.js"), "build"], cwd=root, check=True, capture_output=True
    )
    return root / "dist"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def rendered_grid_alpha(site, theme):
    """The alpha of the grid lines the page paints in Chrome under a forced theme."""
    handler = functools.partial(QuietHandler, directory=str(site))
    with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        threading.Thread(target=server.serve_forever, daemon=True).start()
        browser = shutil.which("google-chrome") or shutil.which("chromium")
        assert browser, "headless Chrome is required"
        dom = subprocess.run(
            [browser, "--headless=new", "--no-sandbox", "--disable-gpu", "--virtual-time-budget=3000", "--dump-dom",
             f"http://127.0.0.1:{server.server_port}/index.html#{theme}"],
            check=True, capture_output=True, text=True, timeout=60,
        ).stdout
        server.shutdown()
    painted = re.search(r"<title>([^<]*)</title>", dom).group(1)
    alpha = re.search(r"linear-gradient\(.*? / ([\d.]+)\)", painted)
    assert alpha, f"the grid is not painted: {painted!r}"
    return float(alpha.group(1))


@pytest.mark.parametrize("stylesheet_linked", [True, False], ids=["stylesheet-linked-as-file", "stylesheet-bundled-by-the-build"])
@pytest.mark.parametrize("theme", GLOW_ALPHA_BY_THEME)
def test_grid_of_the_production_built_page_is_painted_with_the_theme_mix_whether_the_stylesheet_is_linked_or_bundled(
    tarball, tmp_path, stylesheet_linked, theme
):
    site = build_consumer(tarball, tmp_path, stylesheet_linked)
    assert rendered_grid_alpha(site, theme) == pytest.approx(GLOW_ALPHA_BY_THEME[theme], abs=0.005)
