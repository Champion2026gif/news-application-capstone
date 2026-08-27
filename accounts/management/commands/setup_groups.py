"""
Creates the Reader, Editor and Journalist groups and assigns them the
model-level permissions described in the brief:

    Reader     -> can only VIEW articles and newsletters.
    Editor     -> can VIEW, UPDATE, DELETE articles and newsletters,
                  and can APPROVE articles (custom permission).
    Journalist -> can CREATE, VIEW, UPDATE, DELETE articles and newsletters.

Run with:  python manage.py setup_groups
This is safe to re-run (idempotent) and is also invoked automatically
after migrations via accounts/apps.py -> post_migrate signal is NOT used
here on purpose (custom permissions must exist first), so it is a
standalone management command instead - run it once after migrate.
"""
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

from articles.models import Article, Newsletter


class Command(BaseCommand):
    help = "Create Reader/Editor/Journalist groups with correct permissions."

    def handle(self, *args, **options):
        article_ct = ContentType.objects.get_for_model(Article)
        newsletter_ct = ContentType.objects.get_for_model(Newsletter)

        def perm(codename, ct):
            return Permission.objects.get(codename=codename, content_type=ct)

        reader_perms = [
            perm("view_article", article_ct),
            perm("view_newsletter", newsletter_ct),
        ]

        editor_perms = [
            perm("view_article", article_ct),
            perm("change_article", article_ct),
            perm("delete_article", article_ct),
            perm("can_approve_article", article_ct),
            perm("view_newsletter", newsletter_ct),
            perm("change_newsletter", newsletter_ct),
            perm("delete_newsletter", newsletter_ct),
        ]

        journalist_perms = [
            perm("add_article", article_ct),
            perm("view_article", article_ct),
            perm("change_article", article_ct),
            perm("delete_article", article_ct),
            perm("add_newsletter", newsletter_ct),
            perm("view_newsletter", newsletter_ct),
            perm("change_newsletter", newsletter_ct),
            perm("delete_newsletter", newsletter_ct),
        ]

        groups_map = {
            "Reader": reader_perms,
            "Editor": editor_perms,
            "Journalist": journalist_perms,
        }

        for name, perms in groups_map.items():
            group, created = Group.objects.get_or_create(name=name)
            group.permissions.set(perms)
            verb = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{verb} group '{name}' with {len(perms)} permissions."))

        self.stdout.write(self.style.SUCCESS("Group/permission setup complete."))
