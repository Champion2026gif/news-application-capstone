"""
Core content models for the News Application.

This module defines Publisher, Article, and Newsletter models.

The models use normalised Django relationships, including foreign keys
and many-to-many relationships, to connect publishers, users, articles,
and newsletters without duplicating data.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class Publisher(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="editor_publishers",
        limit_choices_to={"role": "EDITOR"},
    )
    journalists = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="journalist_publishers",
        limit_choices_to={"role": "JOURNALIST"},
    )

    def __str__(self):
        return self.name


class Article(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="authored_articles",
        limit_choices_to={"role": "JOURNALIST"},
        help_text="The journalist who wrote this article.",
    )
    # Nullable: an article with publisher=None is an INDEPENDENT article
    # written directly by the journalist. An article with a publisher is
    # publisher content.
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        related_name="articles",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="approved_articles",
        null=True,
        blank=True,
        limit_choices_to={"role": "EDITOR"},
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        permissions = [
            ("can_approve_article", "Can approve article"),
        ]

    def __str__(self):
        return self.title

    def approve(self, editor):
        """Mark the article approved by the given editor and save."""
        self.approved = True
        self.approved_by = editor
        self.approved_at = timezone.now()
        self.save()


class Newsletter(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="authored_newsletters",
        help_text="Journalist or Editor who curated this newsletter.",
    )
    articles = models.ManyToManyField(Article, blank=True, related_name="newsletters")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
