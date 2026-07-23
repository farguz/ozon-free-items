import re

from bs4 import BeautifulSoup


def main():
    print('[*] Start reading ozon_drission_page.html...')
    with open('ozon_drission_page.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    product_links = soup.find_all('a', href=re.compile(r'/product/'))

    seen_urls = set()
    unique_products = []

    for link in product_links:
        href = link.get('href')
        clean_href = href.split('?')[0] if href else ''
        if not clean_href or '/product/' not in clean_href:
            continue

        if clean_href in seen_urls:
            continue
        seen_urls.add(clean_href)

        card = link.parent
        while card:
            if card.name in ['div', 'article', 'li']:
                text = card.get_text()
                if '₽' in text:
                    links_inside = card.find_all('a', href=re.compile(r'/product/'))
                    unique_links_in_card = {l.get('href', '').split('?')[0] for l in links_inside}
                    if len(unique_links_in_card) <= 2:
                        break
            card = card.parent

        if not card:
            card = link.find_parent('div') or link

        card_text = card.get_text(separator=' | ', strip=True) if card else ''

        texts = [t.strip() for t in card.stripped_strings if t.strip()]

        title = ''
        potential_titles = []
        for t in texts:
            if len(t) > 12 and not re.search(
                r'₽|баллов|отзыв|скидка|осталось|доставка|балл|продавец', t, re.IGNORECASE
            ):
                if re.search(r'[а-яА-ЯёЁa-zA-Z]', t):
                    potential_titles.append(t)

        if potential_titles:
            title = max(potential_titles, key=len)

        if not title or len(title) < 5:
            match = re.search(r'/product/(.*?)-\d+/', clean_href)
            if match:
                title = match.group(1).replace('-', ' ').capitalize()

        title = re.sub(r'^\d+\s+баллов?\s+за\s+отзыв', '', title, flags=re.IGNORECASE).strip()

        points_match = re.search(r'(\d+)\s+баллов?\s+за\s+отзыв', card_text, re.IGNORECASE)
        points = points_match.group(0) if points_match else 'No bonuses'

        prices = re.findall(r'(\d[\d\s]*\s*₽)', card_text)
        clean_prices = []
        for p in prices:
            p_clean = p.strip()
            if p_clean not in clean_prices:
                clean_prices.append(p_clean)

        current_price = clean_prices[0] if len(clean_prices) > 0 else 'Price not found'
        old_price = clean_prices[1] if len(clean_prices) > 1 else ''

        unique_products.append(
            {
                'title': title,
                'url': f'https://www.ozon.ru{clean_href}',
                'points': points,
                'price': current_price,
                'old_price': old_price,
            }
        )

    print(f'\n[*] Success, unique items: {len(unique_products)}\n')

    for i, prod in enumerate(unique_products, 1):
        print(f'--- Item #{i} ---')
        print(f'Name: {prod["title"]}')
        print(f'Link: {prod["url"]}')
        print(f'Bonuses: {prod["points"]}')
        print(f'Price: {prod["price"]}' + (f' (before: {prod["old_price"]})' if prod['old_price'] else ''))
        print()


if __name__ == '__main__':
    main()
