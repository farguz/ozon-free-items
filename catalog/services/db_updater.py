import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from catalog.models import Category, ParseLog, PriceHistory, Product

logger = logging.getLogger(__name__)


def sync_products(
    category: Category,
    raw_products: list[dict],
    pages_parsed: int = 0,
) -> ParseLog:
    """Sync with postgres"""
    log = ParseLog(category=category, status=ParseLog.Status.RUNNING)
    log.save()

    try:
        with transaction.atomic():
            now = timezone.now()
            seen_skus: set[int] = set()
            items_price_changed = 0

            existing = {p.sku: p for p in Product.objects.filter(category=category)}

            for raw in raw_products:
                sku = raw['sku']
                seen_skus.add(sku)

                product = existing.get(sku)

                if product:
                    if _update_product(product, raw, now):
                        items_price_changed += 1
                else:
                    _create_product(category, raw)

            # Soft-delete
            deactivated = Product.objects.filter(
                category=category,
                is_active=True,
            ).exclude(sku__in=seen_skus)
            deactivated.update(is_active=False, last_seen_at=now)

            # ParseLog
            log.items_found = len(raw_products)
            log.items_created = len(raw_products) - len(seen_skus & existing.keys())
            log.items_updated = len(seen_skus & existing.keys())
            log.items_price_changed_count = items_price_changed
            log.items_deactivated = deactivated.count()
            log.pages_parsed = pages_parsed
            log.status = ParseLog.Status.SUCCESS
            log.finished_at = timezone.now()
            log.save()

            # Category
            category.last_parsed_at = now
            category.save(update_fields=['last_parsed_at'])

    except Exception:
        logger.exception('Category sync errot, category=%s', category.name)
        log.status = ParseLog.Status.FAILED
        log.error_message = 'Check logs'
        log.finished_at = timezone.now()
        log.save()
        raise

    return log


def _create_product(category: Category, raw: dict) -> None:
    """Create product & PriceHistory."""
    price = raw['current_price'] or Decimal('0')
    points = raw['review_points']

    product = Product.objects.create(
        sku=raw['sku'],
        category=category,
        name=raw.get('name', ''),
        url=raw.get('url', ''),
        image_url=raw.get('image_url', ''),
        brand=raw.get('brand_logo_url', ''),
        current_price=price,
        original_price=raw.get('original_price'),
        discount_percent=raw.get('discount_percent'),
        review_points=points,
        real_price=price - Decimal(str(points)),
        points_ratio=float(points / price * 100) if price > 0 else 0.0,
        rating=raw.get('rating'),
        reviews_count=raw.get('reviews_count', 0),
        stock=raw.get('stock'),
        delivery_date=raw.get('delivery_date', ''),
        badge=raw.get('badge', ''),
    )

    PriceHistory.objects.create(
        product=product,
        price=price,
        original_price=raw.get('original_price'),
        review_points=points,
        stock=raw.get('stock'),
    )


def _update_product(product: Product, raw: dict, now: timezone) -> bool:
    """Update product, return True if changed"""
    new_price = raw['current_price'] or Decimal('0')
    new_points = raw['review_points']

    price_changed = product.current_price != new_price or product.review_points != new_points

    product.name = raw.get('name') or product.name
    product.url = raw.get('url') or product.url
    product.image_url = raw.get('image_url', product.image_url)
    product.brand = raw.get('brand_logo_url', product.brand)
    product.current_price = new_price
    product.original_price = raw.get('original_price', product.original_price)
    product.discount_percent = raw.get('discount_percent', product.discount_percent)
    product.review_points = new_points
    product.rating = raw.get('rating', product.rating)
    product.reviews_count = raw.get('reviews_count', product.reviews_count)
    product.stock = raw.get('stock', product.stock)
    product.delivery_date = raw.get('delivery_date', product.delivery_date)
    product.badge = raw.get('badge', product.badge)
    product.is_active = True

    if price_changed:
        product.last_price_change = now

    product.save()

    if price_changed:
        PriceHistory.objects.create(
            product=product,
            price=new_price,
            original_price=raw.get('original_price'),
            review_points=new_points,
            stock=raw.get('stock'),
        )

    return price_changed
