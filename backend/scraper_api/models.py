

# Create your models here.
from django.db import models

class SiteSource(models.Model):
    class SearchType(models.TextChoices):
        GET = 'GET', 'GET Parameter'
        POST = 'POST', 'POST API'

    name = models.CharField(max_length=100, unique=True)
    base_url = models.URLField(max_length=255, help_text="The base URL, e.g., 'https://vegamovies.talk'")
    is_active = models.BooleanField(default=True, help_text="Include this site in searches")
    
    # --- Search Logic ---
    search_type = models.CharField(max_length=4, choices=SearchType.choices, default=SearchType.GET)
    search_endpoint = models.CharField(
        max_length=255, 
        help_text="The search path. Use %QUERY% as placeholder, e.g., '/?s=%QUERY%&layout=talk'"
    )
    post_payload_template = models.TextField(
        blank=True, 
        null=True,
        help_text="For POST type only. A JSON/form-data template with '%QUERY%' as placeholder."
    )
    requires_playwright = models.BooleanField(
        default=False, 
        help_text="Check this if the site is protected by Cloudflare or requires JS rendering"
    )

    # --- CSS Selector "Pattern" ---
    result_container_selector = models.CharField(
        max_length=255, 
        help_text="CSS selector for the parent container of a single result (e.g., 'article.post-item')"
    )
    result_title_selector = models.CharField(
        max_length=255, 
        help_text="CSS selector for the title text (e.g., 'h2.title a')"
    )
    result_link_selector = models.CharField(
        max_length=255, 
        help_text="CSS selector for the result's <a> tag (e.g., 'h2.title a')"
    )
    result_poster_selector = models.CharField(
        max_length=255, 
        help_text="CSS selector for the <img> tag (e.g., 'img.post-image')"
    )
    result_poster_attribute = models.CharField(
        max_length=50, 
        default='src', 
        help_text="The attribute holding the image URL (e.g., 'src', 'data-src')"
    )

    def __str__(self):
        return self.name

