import os
import time

from dotenv import load_dotenv
from DrissionPage import ChromiumOptions, ChromiumPage

load_dotenv()

browser_path = os.getenv('CHROME_EXECUTABLE_PATH') or None
category_url = os.getenv('OZON_CATEGORY_URL') or None


def main():
    url = category_url

    co = ChromiumOptions()
    co.set_browser_path(browser_path)
    co.set_argument('--no-sandbox')

    page = ChromiumPage(co)

    try:
        print(f'[*] Start: {url}')
        page.get(url)

        print('[*] User imitation delay...')
        time.sleep(5)

        print('[*] Page scroll...')
        page.scroll.down(1000)
        time.sleep(3)

        title = page.title
        print(f'[*] Title: {title}')

        if 'Похоже, нет соединения' in title or 'Ой!' in title:
            print('[*] Website detects our behaviour')
        else:
            print('[*] Success')

            html = page.html
            with open('ozon_drission_page.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print("[*] HTML saved to 'ozon_drission_page.html'")

    finally:
        page.quit()


if __name__ == '__main__':
    main()
