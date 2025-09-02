import pytest
from playwright.sync_api import sync_playwright


pytestmark = pytest.mark.ui


def test_promo_links_clickable_open_in_new_tab(serve_app):
    # Content with three markdown links rendered under the image
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
            browser = p.chromium.launch()
            page = browser.new_page()

            # Сначала загружаем локальную страницу, затем блокируем внешнюю сеть
            page.goto(f"http://127.0.0.1:{port}/static/index.html")
            page.wait_for_selector("#promoLinks a")

            # Блокируем внешние переходы после загрузки локальной страницы
            page.route("**/*", lambda route: route.abort())

            links = page.query_selector_all("#promoLinks a")
            assert len(links) >= 3

            for link in links:
                href = link.get_attribute("href")
                target = link.get_attribute("target")
                rel = link.get_attribute("rel")
                assert href and href.startswith("http")
                assert target == "_blank"
                assert rel and "noopener" in rel

                with page.expect_popup() as popup_info:
                    link.click()
                popup = popup_info.value
                # Even with aborted network we still get a popup window
                assert popup is not None
                popup.close()

            browser.close()
