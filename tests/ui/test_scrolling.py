import pytest

from playwright.sync_api import Page, sync_playwright


pytestmark = pytest.mark.ui


def test_message_scrolling_works(serve_app):
    long_lines = "\n".join([f"• Линия {i} текста с событием" for i in range(1, 200)])
    app, port = serve_app(long_lines, image_data=None)

    from tests.ui.conftest import _run_uvicorn as run_uvicorn

    with run_uvicorn(app, port):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"http://127.0.0.1:{port}/static/index.html")

            # Wait content to render
            page.wait_for_selector("#messageText")

            # Ensure content is taller than viewport
            scroll_h = page.eval_on_selector(".message-scroll", "el => el.clientHeight")
            total_h = page.eval_on_selector("#messageText", "el => el.scrollHeight")
            assert total_h > scroll_h, (total_h, scroll_h)

            # Check animation name set
            anim = page.eval_on_selector(
                ".marquee",
                "el => getComputedStyle(el).animationName",
            )
            assert anim != "none"

            # Ensure transform changes over time
            t1 = page.eval_on_selector(
                ".marquee", "el => getComputedStyle(el).transform",
            )
            page.wait_for_timeout(1000)
            t2 = page.eval_on_selector(
                ".marquee", "el => getComputedStyle(el).transform",
            )
            assert t1 != t2
            browser.close()
