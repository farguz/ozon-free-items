import html as html_lib
import json
import logging
import re
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class OzonHtmlParser:
    """Parse Ozon category page from state-tileGridDesktop JSON"""

    OZON_HOST = 'https://www.ozon.ru'

    def parse(self, html_content: str) -> list[dict]:
        products = self._parse_json_state(html_content)
        if products:
            return products
        return self._parse_html_fallback(html_content)

    def get_next_page_url(self, html_content: str) -> str | None:
        """Return next page (better do not use, endless scroll mostly)"""
        match = re.search(
            r'id="state-infiniteVirtualPaginator-[^"]+"\s+data-state="([^"]+)"',
            html_content,
        )
        if not match:
            return None

        raw_json = html_lib.unescape(match.group(1))
        paginator = json.loads(raw_json)
        next_page = paginator.get('nextPage')
        prev_page = paginator.get('prevPage')
        if next_page and next_page != prev_page:
            return f'{self.OZON_HOST}{next_page}'
        return None

    def _parse_json_state(self, html_content: str) -> list[dict]:
        match = re.search(
            r'id="state-tileGridDesktop-[^"]+"\s+data-state="([^"]+)"',
            html_content,
        )
        if not match:
            return []

        raw_json = html_lib.unescape(match.group(1))

        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError:
            logger.warning('Wrong JSON')
            return []

        products = []
        for item in data.get('items', []):
            try:
                products.append(self._parse_item(item))
            except (KeyError, TypeError, ValueError, InvalidOperation) as e:
                logger.warning(f'Error during parsing item= {item.get("name")}: {e}')
                continue
        return products

    def _parse_item(self, item: dict) -> dict:
        sku = int(item['sku'])
        url_path = item['action']['link'].split('?')[0]

        return {
            'sku': sku,
            'url': f'{self.OZON_HOST}{url_path}',
            'name': self._extract_name(item),
            'current_price': self._extract_current_price(item),
            'original_price': self._extract_original_price(item),
            'discount_percent': self._extract_discount(item),
            'review_points': self._extract_points(item),
            'rating': self._extract_rating(item),
            'reviews_count': self._extract_reviews_count(item),
            'stock': self._extract_stock(item),
            'delivery_date': self._extract_delivery(item),
            'image_url': self._extract_image(item),
            'badge': self._extract_badge(item),
            'brand_logo_url': self._extract_brand_logo(item),
        }

    def _extract_name(self, item: dict) -> str:
        for state in item.get('mainState', []):
            if state.get('id') == 'name':
                return state['textDS']['text']
        return ''

    def _extract_current_price(self, item: dict) -> Decimal:
        state = self._find_price_state(item)
        if not state:
            return Decimal('0')
        prices = state['priceV2']['price']
        if not prices:
            return Decimal('0')
        return self._parse_price(prices[0]['text'])

    def _extract_original_price(self, item: dict) -> Decimal | None:
        state = self._find_price_state(item)
        if not state:
            return None
        prices = state['priceV2']['price']
        if len(prices) < 2:
            return None
        return self._parse_price(prices[1]['text'])

    def _extract_discount(self, item: dict) -> int | None:
        state = self._find_price_state(item)
        if not state:
            return None
        discount = state['priceV2'].get('discount', '')
        match = re.search(r'(\d+)', discount)
        return int(match.group(1)) if match else None

    def _extract_points(self, item: dict) -> int:
        badge = item.get('tileImage', {}).get('leftBottomBadgeV2', {}).get('text', '')
        match = re.search(r'(\d+)\s+балл', badge)
        return int(match.group(1)) if match else 0

    def _extract_rating(self, item: dict) -> Decimal | None:
        rating, _ = self._extract_rating_block(item)
        return rating

    def _extract_reviews_count(self, item: dict) -> int:
        _, count = self._extract_rating_block(item)
        return count

    def _extract_stock(self, item: dict) -> int | None:
        for state in item.get('mainState', []):
            if state.get('type') != 'textDS':
                continue
            test_id = state.get('textDS', {}).get('testInfo', {}).get('automatizationId', '')
            if test_id == 'tile-blackFridayStockbar':
                match = re.search(r'(\d+)', state['textDS']['text'])
                return int(match.group(1)) if match else None
        return None

    def _extract_delivery(self, item: dict) -> str:
        return (
            item.get('multiButton', {})
            .get('ozonButton', {})
            .get('addToCart', {})
            .get('actionButton', {})
            .get('title', '')
        )

    def _extract_image(self, item: dict) -> str:
        images = item.get('tileImage', {}).get('items', [])
        if not images:
            return ''
        return images[0].get('image', {}).get('link', '')

    def _extract_badge(self, item: dict) -> str:
        return item.get('tileImage', {}).get('leftBottomBadgeV2', {}).get('text', '')

    def _extract_brand_logo(self, item: dict) -> str:
        return (item.get('brandLogo') or {}).get('logo', '')

    def _find_price_state(self, item: dict) -> dict | None:
        for state in item.get('mainState', []):
            if state.get('type') == 'priceV2':
                return state
        return None

    def _extract_rating_block(self, item: dict) -> tuple[Decimal | None, int]:
        rating = None
        reviews_count = 0

        for state in item.get('mainState', []):
            if state.get('type') != 'labelListV2':
                continue
            info = state.get('labelListV2', {})
            test_id = info.get('testInfo', {}).get('automatizationId', '')
            if test_id != 'tile-list-rating':
                continue

            for row in info.get('items', []):
                if row.get('type') != 'text':
                    continue
                text = row['text']['text']

                if rating is None and re.match(r'^\d+\.\d+$', text):
                    try:
                        rating = Decimal(text)
                    except InvalidOperation:
                        logger.info('no rating')
                        pass
                elif 'отзыв' in text.lower():
                    match = re.search(r'([\d\s]+)', text)
                    if match:
                        reviews_count = int(match.group(1).replace(' ', ''))

        return rating, reviews_count

    @staticmethod
    def _parse_price(text: str) -> Decimal:
        """str2decimal"""
        cleaned = text.replace(' ', '').replace(',', '.')
        cleaned = re.sub(r'[^\d.]', '', cleaned)
        return Decimal(cleaned)

    def _parse_html_fallback(self, html_content: str) -> list[dict]:
        """Fallback if no JSON state."""
        soup = BeautifulSoup(html_content, 'html.parser')
        products = []
        seen = set()

        for link in soup.find_all('a', href=re.compile(r'/product/')):
            href = (link.get('href') or '').split('?')[0]
            if not href or '/product/' not in href or href in seen:
                continue
            seen.add(href)

            sku_match = re.search(r'-(\d+)/?$', href)
            if not sku_match:
                continue

            products.append(
                {
                    'sku': int(sku_match.group(1)),
                    'url': f'{self.OZON_HOST}{href}',
                    'name': link.get_text(strip=True),
                }
            )

        return products
