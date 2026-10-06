"""Start Streamlit, verify its rendered dashboard, and save a portfolio screenshot."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def capture(output: Path, port: int, require_date: str | None) -> None:
    url = f"http://127.0.0.1:{port}"
    environment = os.environ.copy()
    for name in ("ADZUNA_APP_ID", "ADZUNA_APP_KEY"):
        environment.pop(name, None)
    with tempfile.TemporaryFile(mode="w+b") as log:
        server = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py"),
             "--server.headless=true", "--server.address=127.0.0.1",
             f"--server.port={port}", "--browser.gatherUsageStats=false"],
            cwd=ROOT, env=environment, stdout=log, stderr=log,
        )
        try:
            deadline = time.monotonic() + 60
            while True:
                if server.poll() is not None:
                    raise RuntimeError("Streamlit exited before becoming healthy.")
                try:
                    with urlopen(url + "/_stcore/health", timeout=2) as response:
                        if response.status == 200:
                            break
                except (URLError, TimeoutError, OSError):
                    pass
                if time.monotonic() >= deadline:
                    raise TimeoutError("Streamlit did not become healthy within 60 seconds.")
                time.sleep(0.5)
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                try:
                    page = browser.new_page(viewport={"width": 1600, "height": 1600}, device_scale_factor=1)
                    page.set_default_timeout(60000)
                    page.goto(url, wait_until="domcontentloaded")
                    print("Streamlit is healthy; waiting for the dashboard.", flush=True)
                    marker = page.locator("#dashboard-ready")
                    marker.wait_for(state="attached")
                    if page.locator('[data-testid="stException"]').count():
                        raise RuntimeError("The dashboard rendered a Streamlit exception.")
                    if require_date:
                        if marker.get_attribute("data-synthetic") != "false":
                            raise RuntimeError("Refresh rendered synthetic data instead of the live extract.")
                        if marker.get_attribute("data-retrieved") != require_date:
                            raise RuntimeError("Refresh rendered an extract from the wrong date.")
                    # The pay panel may show an honest no-data message; the other
                    # three charts must be rendered before we take the screenshot.
                    page.wait_for_function("""() => {
                        const plots = [...document.querySelectorAll('.js-plotly-plot')];
                        return plots.length >= 3 && plots.every(p => p._fullLayout && p.querySelector('.main-svg'));
                    }""")
                    page.evaluate("document.fonts.ready")
                    height = page.locator('[data-testid="stMain"]').evaluate("el => el.scrollHeight")
                    page.set_viewport_size({"width": 1600, "height": min(10000, max(1600, height + 100))})
                    page.wait_for_function("""() => [...document.querySelectorAll('.js-plotly-plot')]
                        .every(p => p._fullLayout && p.querySelector('.main-svg')?.getBoundingClientRect().width > 0)""")
                    page.evaluate("() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
                    print("Fresh data and charts verified; saving screenshot.", flush=True)
                    output.parent.mkdir(parents=True, exist_ok=True)
                    page.screenshot(path=str(output), full_page=True, animations="disabled")
                    print(f"Dashboard screenshot saved to {output.relative_to(ROOT) if output.is_relative_to(ROOT) else output}")
                finally:
                    browser.close()
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=10)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "Screenshot" / "dashboard.png")
    parser.add_argument("--port", type=int, default=8501)
    parser.add_argument("--require-date", help="Fail unless the live extract has this ISO retrieval date.")
    args = parser.parse_args()
    capture(args.output.resolve(), args.port, args.require_date)


if __name__ == "__main__":
    main()
