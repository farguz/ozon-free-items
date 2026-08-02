from django.contrib import admin

from .models import Category, NotificationHistory, ParseLog, PriceHistory, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'url', 'is_active', 'last_parsed_at', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'url')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('last_parsed_at', 'created_at', 'updated_at')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'sku',
        'name',
        'category',
        'current_price',
        'review_points',
        'real_price',
        'points_ratio',
        'is_active',
        'is_purchased',
    )
    list_filter = ('is_active', 'is_purchased', 'is_not_interested', 'category')
    search_fields = ('sku', 'name')
    readonly_fields = (
        'real_price',
        'points_ratio',
        'first_seen_at',
        'last_seen_at',
        'last_price_change',
    )
    list_editable = ('is_purchased',)
    list_per_page = 50
    list_select_related = ('category',)
    ordering = ('-last_seen_at',)


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'price', 'original_price', 'review_points', 'stock', 'recorded_at')
    list_filter = ('recorded_at',)
    search_fields = ('product__sku__exact', 'product__name')
    readonly_fields = ('recorded_at',)
    list_select_related = ('product',)
    list_per_page = 100


@admin.register(ParseLog)
class ParseLogAdmin(admin.ModelAdmin):
    list_display = (
        'category',
        'status',
        'pages_parsed',
        'items_found',
        'items_created',
        'items_updated',
        'items_deactivated',
        'started_at',
        'finished_at',
        'duration_seconds',
    )
    list_filter = ('status', 'category')
    readonly_fields = (
        'category',
        'status',
        'pages_parsed',
        'items_found',
        'items_created',
        'items_updated',
        'items_deactivated',
        'items_price_changed_count',
        'error_message',
        'started_at',
        'finished_at',
    )
    list_per_page = 50
    list_select_related = ('category',)
    date_hierarchy = 'started_at'


@admin.register(NotificationHistory)
class NotificationHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'message', 'sent_at')
    list_filter = ('sent_at',)
    search_fields = ('product__sku', 'product__name')
    readonly_fields = ('sent_at',)
    list_select_related = ('product',)
