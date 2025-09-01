import pytest
from playwright.sync_api import sync_playwright


pytestmark = pytest.mark.ui


def test_layout_heights_and_header_static(serve_app):
    long_lines = "\n".join([f"• Новость {i}" for i in range(1, 120)])
    app, port = serve_app(long_lines)

    from tests.ui.conftest import _run_uvicorn as run_uvicorn

    with run_uvicorn(app, port):
        with sync_playwright() as p:
            page = p.chromium.launch().new_page()
            page.goto(f"http://127.0.0.1:{port}/static/index.html")
            page.wait_for_selector("#timeHeader")

            left_h = page.eval_on_selector(".telegram-image", "el => el.offsetHeight")
            right_h = page.eval_on_selector(".message-content", "el => el.offsetHeight")
            assert abs(left_h - right_h) <= 3

            # header should be visible and not transformed
            transform = page.eval_on_selector("#timeHeader", "el => getComputedStyle(el).transform")
            assert transform == "none"


def test_promo_links_extracted(serve_app):
    content = (
        "• Первая строка новости\n\n"
        "[Свежий договорняковый дайджест.](https://telegra.ph/x) "
        "[Поддержать проект.](https://boosty.to/y) "
        "[Часы судного договорняка.](https://t.me/dooms_deal_clock/11)\n"
    )
    app, port = serve_app(content)

    from tests.ui.conftest import _run_uvicorn as run_uvicorn

    with run_uvicorn(app, port):
        with sync_playwright() as p:
            page = p.chromium.launch().new_page()
            page.goto(f"http://127.0.0.1:{port}/static/index.html")
            page.wait_for_selector("#promoLinks")

            # Links rendered under image
            links_count = page.eval_on_selector_all("#promoLinks a", "els => els.length")
            assert links_count >= 2

            # Footer texts removed from the right message area
            body_text = page.text_content("#messageText") or ""
            assert "Свежий договорняковый дайджест" not in body_text
            assert "Поддержать проект" not in body_text
            assert "Часы судного договорняка" not in body_text
