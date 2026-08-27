"""
Custom user model for the News Application.

The application uses a single CustomUser model with a role field for
Reader, Editor, and Journalist accounts.

Role-specific relationships are represented using Django relationships,
including subscriptions for readers and authored content for journalists.
This keeps authentication simple while supporting role-based behaviour.
"""
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    READER = "READER", "Reader"
    EDITOR = "EDITOR", "Editor"
    JOURNALIST = "JOURNALIST", "Journalist"


class CustomUser(AbstractUser):
    """
    Extends Django's AbstractUser with a role field and role-specific
    subscription fields.
    """

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.READER,
        help_text="Determines which permissions group the user belongs to.",
    )

    # --- Reader-only fields -------------------------------------------------
    # A reader can subscribe to publishers and to individual journalists.
    subscriptions_publishers = models.ManyToManyField(
        "articles.Publisher",
        blank=True,
        related_name="subscribed_readers",
        help_text="Publishers this reader is subscribed to. Reader role only.",
    )
    subscriptions_journalists = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="journalist_subscribers",
        limit_choices_to={"role": Role.JOURNALIST},
        help_text="Journalists this reader is subscribed to. Reader role only.",
    )

    # NOTE on Journalist-only fields ("Articles that the user has published
    # independently" / "Newsletters that the user has published
    # independently"): these are implemented as REVERSE RELATIONS rather
    # than duplicate ManyToMany/ForeignKey fields on CustomUser, per the
    # brief's "ForeignKey or Reverse relation" allowance. They are exposed
    # as the properties `independent_articles` and `independent_newsletters`
    # below, which read from Article.author / Newsletter.author
    # (related_name="authored_articles" / "authored_newsletters").

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    # -- role-aware helpers ---------------------------------------------
    @property
    def is_reader(self):
        return self.role == Role.READER

    @property
    def is_editor(self):
        return self.role == Role.EDITOR

    @property
    def is_journalist(self):
        return self.role == Role.JOURNALIST

    @property
    def independent_articles(self):
        """Articles this user has published without a publisher (Journalist)."""
        return self.authored_articles.filter(publisher__isnull=True)

    @property
    def independent_newsletters(self):
        """Newsletters authored by this user (Journalist/Editor)."""
        return self.authored_newsletters.all()

    def save(self, *args, **kwargs):
        """
        Enforce the brief's rule: "If a user has a Journalist role, the
        program should assign the fields for the reader a value of 'None',
        and vice versa."

        ManyToMany fields cannot be set before the row has a primary key,
        so the M2M clearing happens in the post_save signal
        (accounts/signals.py) which runs after this save() completes.
        """
        super().save(*args, **kwargs)
