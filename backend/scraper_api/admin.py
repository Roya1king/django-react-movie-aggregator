
# Register your models here.
from django.contrib import admin
from .models import SiteSource

# This "registers" your SiteSource model with the Django admin page
@admin.register(SiteSource)
class SiteSourceAdmin(admin.ModelAdmin):
    # Columns to display in the list view
    list_display = ('name', 'is_active', 'search_type', 'requires_playwright', 'base_url')
    # Filters on the right-hand side
    list_filter = ('is_active', 'search_type', 'requires_playwright')
    # Search bar fields
    search_fields = ('name', 'base_url')
    
    # How the "Edit" page is organized
    fieldsets = (
        (None, {
            'fields': ('name', 'base_url', 'is_active')
        }),
        ('Search Logic', {
            'fields': ('search_type', 'search_endpoint', 'post_payload_template', 'requires_playwright')
        }),
        ('Result Pattern (CSS Selectors)', {
            'fields': ('result_container_selector', 'result_title_selector', 'result_link_selector', 'result_poster_selector', 'result_poster_attribute')
        }),
    )
