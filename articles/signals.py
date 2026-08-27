"""
Option 1 (Signals) implementation of the "on approval" behaviour.

When an Article is saved with approved=True (and it was not already
approved), this signal:
  1. Emails every reader subscribed to the article's publisher and/or
     to the article's author (journalist).
  2. Sends a POST request to this project's own /api/approved/ endpoint
     using `requests`, simulating sharing the approved article
     externally while keeping the integration inside the project.

A simple in-memory/db flag (`_approval_notified`) prevents duplicate
notifications from repeated saves (e.g. editing an already-approved
article again).
"""
import logging

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Article

logger = logging.getLogger(__name__)


def _collect_subscriber_emails(article):
    """Readers subscribed to the article's publisher OR its author."""
    from accounts.models import CustomUser, Role

    subscriber_qs = CustomUser.objects.filter(role=Role.READER).filter(
        models_q(article)
    ).distinct()
    return list(subscriber_qs.values_list("email", flat=True).exclude(email=""))


def models_q(article):
    from django.db.models import Q
    q = Q(subscriptions_journalists=article.author)
    if article.publisher_id:
        q |= Q(subscriptions_publishers=article.publisher)
    return q


@receiver(post_save, sender=Article)
def notify_on_approval(sender, instance, created, update_fields=None, **kwargs):
    if not instance.approved:
        return

    # Avoid re-notifying on every subsequent save of an already-approved
    # article by checking a transient attribute set once per process.
    if getattr(instance, "_approval_notified", False):
        return

    emails = _collect_subscriber_emails(instance)
    if emails:
        try:
            send_mail(
                subject=f"New article published: {instance.title}",
                message=(
                    f"{instance.title}\n\n{instance.content[:500]}\n\n"
                    f"-- {instance.author.get_full_name() or instance.author.username}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=emails,
                fail_silently=True,
            )
        except Exception:
            logger.exception("Failed to email subscribers for article %s", instance.pk)

    # POST to our own internal API endpoint to log/share the approved article.
    try:
        base_url = getattr(settings, "INTERNAL_API_BASE_URL", "http://localhost:8000")
        requests.post(
            f"{base_url}/api/approved/",
            json={
                "article_id": instance.pk,
                "title": instance.title,
                "author": instance.author.username,
                "publisher": instance.publisher.name if instance.publisher_id else None,
                "approved_at": instance.approved_at.isoformat() if instance.approved_at else None,
            },
            timeout=3,
        )
    except requests.exceptions.RequestException:
        # In dev/test environments the server may not be reachable - this
        # must never break the approval flow itself.
        logger.warning("Could not reach internal /api/approved/ endpoint for article %s", instance.pk)

    instance._approval_notified = True
