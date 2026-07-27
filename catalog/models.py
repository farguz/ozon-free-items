from decimal import Decimal

from django.db import models
from django.utils import timezone


class Category(models.Model):
    """Ozon category for tracking"""

    name = models.CharField(
        'Category name',
        max_length=255,
        blank=True,
    )
    slug = models.SlugField(max_length=255, unique=True)
    url = models.URLField(
        'Link/URL',
        max_length=1024,
        unique=True,
    )
    filter_params = models.JSONField(
        'Filters (JSON)',
        default=dict,
        blank=True,
        help_text='Example {"has_points_from_reviews": true, "delivery": 8}',
    )
    max_pages = models.PositiveIntegerField(
        'Max pages (actually endless scroll?)',
        default=1,
    )
    sort_by = models.CharField(max_length=50, blank=True, default='')
    parse_interval = models.PositiveIntegerField(
        'parse interval at secs',
        default=43200,  # 0.5 days
    )
    is_active = models.BooleanField(
        'Active',
        default=True,
    )
    last_parsed_at = models.DateTimeField(
        'Last time parsed',
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(
        'Created at',
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        'Updated at',
        auto_now=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['last_parsed_at']),
        ]
        ordering = ('name',)
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name or self.url


class Product(models.Model):
    """Ozon item and its current state"""

    sku = models.PositiveBigIntegerField(
        'SKU',
        unique=True,
        db_index=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
    )
    name = models.TextField('Name')
    url = models.URLField('Link/URL', max_length=1024)
    image_url = models.URLField('Image (URL)', max_length=1024, blank=True, default='')
    brand = models.CharField('Brand', max_length=255, blank=True, default='')
    seller = models.CharField('Seller', max_length=255, blank=True, default='')

    current_price = models.DecimalField('Current price', max_digits=10, decimal_places=2)
    original_price = models.DecimalField(
        'Full price before discounts',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    discount_percent = models.PositiveSmallIntegerField(
        'Discount %',
        null=True,
        blank=True,
    )
    review_points = models.PositiveIntegerField('Bonuses 4 reviews', default=0)

    real_price = models.DecimalField('Real price (price-bonuses)', max_digits=10, decimal_places=2, default=0)
    points_ratio = models.FloatField('Freebie ratio (bonuses/price)', default=0.0)

    rating = models.DecimalField(
        "User's rating",
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
    )
    reviews_count = models.PositiveIntegerField('Review count / popularity', default=0)

    stock = models.PositiveIntegerField('Stock', null=True, blank=True)
    delivery_date = models.CharField('Delivery date', max_length=64, blank=True, default='')
    badge = models.CharField('Badge', max_length=128, blank=True, default='')

    is_active = models.BooleanField(
        'Flag for actual/outdated items', default=True, help_text='Are there still bonuses?'
    )
    is_purchased = models.BooleanField(
        'Flag for bought/not yet', default=False, help_text='Have I bought it already? Cause you can review only once'
    )
    is_not_interested = models.BooleanField(
        'Flag for do not track (useless items)', default=False, help_text='Shit items I do not want aka black list'
    )
    first_seen_at = models.DateTimeField('First seen with bonuses', auto_now_add=True)
    last_seen_at = models.DateTimeField('Last seen with bonuses', auto_now=True)
    last_price_change = models.DateTimeField(
        'Last price change datetime',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Item'
        verbose_name_plural = 'Items'
        ordering = ['real_price']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_active', 'real_price']),
            models.Index(fields=['-points_ratio']),
            models.Index(fields=['-last_seen_at']),
        ]

    def save(self, *args, **kwargs):
        self.real_price = self.current_price - Decimal(str(self.review_points))
        if self.current_price > 0:
            self.points_ratio = round(
                float((Decimal(str(self.review_points)) / self.current_price) * 100),
                2,
            )
        else:
            self.points_ratio = 0.0
        super().save(*args, **kwargs)

    def __str__(self):
        return f'[{self.sku}] {self.name[:50]} {self.current_price}₽ ({self.review_points} bonuses)'


class PriceHistory(models.Model):
    """Items price history"""

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='price_history',
        verbose_name='Item',
    )
    price = models.DecimalField('Price', max_digits=10, decimal_places=2)
    original_price = models.DecimalField(
        'Price without discounts', max_digits=10, decimal_places=2, null=True, blank=True
    )
    review_points = models.PositiveIntegerField('Bonuses 4 reviews', default=0)
    stock = models.PositiveIntegerField('Stock', null=True, blank=True)
    recorded_at = models.DateTimeField('Recorded price datetime', auto_now_add=True)

    class Meta:
        verbose_name = 'Price history'
        verbose_name_plural = 'Price histories'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['product', '-recorded_at']),
        ]

    def __str__(self):
        return f'{self.product_id} @ {self.price}₽ ({self.recorded_at.strftime("%d.%m %H:%M")})'


class ParseLog(models.Model):
    class Status(models.TextChoices):
        RUNNING = 'running', 'Running'
        SUCCESS = 'success', 'Success'
        PARTIAL = 'partial', 'Partial'
        FAILED = 'failed', 'Failed'

    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='parse_logs', verbose_name='Category'
    )
    status = models.CharField(
        'Status',
        max_length=16,
        choices=Status.choices,
        default=Status.RUNNING,
    )
    pages_parsed = models.PositiveSmallIntegerField('Pages parsed count', default=0)
    items_found = models.PositiveIntegerField('Items count', default=0)
    items_created = models.PositiveIntegerField('New items found', default=0)
    items_updated = models.PositiveIntegerField('Items updated', default=0)
    items_deactivated = models.PositiveIntegerField('Items cancelled bonuses', default=0)
    items_price_changed_count = models.PositiveIntegerField('Items with new prices', default=0)

    error_message = models.TextField('Error message', blank=True, default='')

    started_at = models.DateTimeField('Parse started', auto_now_add=True)
    finished_at = models.DateTimeField('Parse ended', null=True, blank=True)

    class Meta:
        ordering = ('-started_at',)
        verbose_name = 'Parse log'
        verbose_name_plural = 'Parse logs'
        indexes = [
            models.Index(fields=['category', '-started_at']),
            models.Index(fields=['status']),
        ]

    @property
    def duration_seconds(self):
        """Parse duration"""
        end_time = self.finished_at or timezone.now()
        return round((end_time - self.started_at).total_seconds(), 2)

    def __str__(self):
        cat_name = self.category.name if self.category else '---'
        return f'[{self.get_status_display()}] {cat_name} ({self.started_at.strftime("%d.%m %H:%M")})'


class NotificationHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    message = models.TextField('Message text')
    sent_at = models.DateTimeField(auto_now_add=True)
