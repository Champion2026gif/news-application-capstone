from django.contrib import admin

from .models import ApprovedArticleLog


@admin.register(ApprovedArticleLog)
class ApprovedArticleLogAdmin(admin.ModelAdmin):
    list_display = ("article_id", "title", "author", "publisher", "received_at")
