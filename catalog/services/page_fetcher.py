import logging
import os
import time
from random import uniform

from dotenv import load_dotenv
from DrissionPage import ChromiumOptions, ChromiumPage

load_dotenv()
logger = logging.getLogger(__name__)

BLOCKED_PAGE_TITLES = (
    'Похоже, нет соединения',
    'Ой!',
    'Cloudflare',
)


def fetch_page_html(
    url: str,
    browser_path: str | None = None,
    headless: bool = False,
    scroll_count: int = 5,
) -> str:
    """Func tries to save ozon web page with imitation of user behaviour
    Args:
        url: category URL.
        browser_path: pass (if you use firefox like me).
        headless: headless mode, better do not use.
        scroll_count: pass (max pages analogue).

    Returns:
        Complete HTML page.

    Raises:
        ConnectionError: If Ozon detects bot.
    """
    browser_path = browser_path or os.getenv('CHROME_EXECUTABLE_PATH')

    options = ChromiumOptions()
    if browser_path:
        options.set_browser_path(browser_path)
    if headless:
        options.set_argument('--headless')
    options.set_argument('--no-sandbox')

    page = ChromiumPage(options)
    try:
        logger.info(f'Start fetching page {url}')
        page.get(url)
        time.sleep(uniform(2, 4))

        # few scrolls imitation
        for _ in range(scroll_count):
            page.scroll.down(1000)
            time.sleep(uniform(2, 4))

        # check anti bot defense system
        title = page.title
        if any(text in title for text in BLOCKED_PAGE_TITLES):
            raise ConnectionError(f'Ozon blocked request: "{title}"')

        logger.info(f'HTML fetched successfully {url}')
        return page.html
    except Exception as e:
        logger.error(f'Error during fetching {url}. Exception {e}')
        raise
    finally:
        page.quit()
