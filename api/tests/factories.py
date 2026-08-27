"""Small helpers shared across the API test modules."""
from django.contrib.auth import get_user_model
import io
from django.core.management import call_command

from articles.models import Article, Publisher

User = get_user_model()


def ensure_groups():
    call_command("setup_groups", stdout=io.StringIO())


def create_user(username, role, **extra):
    user = User.objects.create_user(
        username=username,
        password="testpass123",
        email=f"{username}@example.com",
        role=role,
        **extra,
    )
    return user


def create_publisher(name="Daily Times", journalists=None, editors=None):
    pub = Publisher.objects.create(name=name)
    for j in journalists or []:
        pub.journalists.add(j)
    for e in editors or []:
        pub.editors.add(e)
    return pub


def create_article(author, publisher=None, approved=False, title="Test Article"):
    return Article.objects.create(
        title=title,
        content="Some article content.",
        author=author,
        publisher=publisher,
        approved=approved,
    )
