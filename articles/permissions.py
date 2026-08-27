"""
Reusable access-control helpers for the traditional (template-based)
views in this app. DRF endpoints have their own permission classes in
api/permissions.py.
"""
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class EditorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Only users in the Editor group (or superusers) may proceed."""

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name="Editor").exists()

    def handle_no_permission(self):
        from django.core.exceptions import PermissionDenied
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        raise PermissionDenied("Only editors may access this page.")


class JournalistOrEditorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return (
            user.is_superuser
            or user.groups.filter(name__in=["Editor", "Journalist"]).exists()
        )
