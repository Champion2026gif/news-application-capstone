"""
DRF permission classes enforcing role-based authorization:
  - Only journalists may POST (create) articles/newsletters.
  - Only editors (or the owning journalist) may PUT/PATCH.
  - Only editors and journalists may DELETE.
  - Readers get read-only (GET) access.
  - Only editors may hit the approve action.
"""
from rest_framework import permissions


class IsJournalistToCreate(permissions.BasePermission):
    """SAFE methods allowed to any authenticated user; POST requires Journalist role."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        if request.method == "POST":
            return bool(
                request.user
                and request.user.is_authenticated
                and (request.user.is_superuser or request.user.role == "JOURNALIST")
            )
        return True  # other methods handled by IsEditorOrOwnerJournalist


class IsJournalistOrEditorToCreate(permissions.BasePermission):
    """
    Used for Newsletters: per the brief, newsletters may be "edited or
    created by journalists and editors" (unlike Articles, where only
    journalists may POST).
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        if request.method == "POST":
            return bool(
                request.user
                and request.user.is_authenticated
                and (request.user.is_superuser or request.user.role in ("JOURNALIST", "EDITOR"))
            )
        return True


class IsEditorOrOwnerJournalistForWrite(permissions.BasePermission):
    """
    PUT/PATCH: editors, or the journalist who authored the object.
    DELETE: editors, or the journalist who authored the object.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser or user.role == "EDITOR":
            return True
        is_owner = getattr(obj, "author_id", None) == user.id
        if request.method in permissions.SAFE_METHODS:
            # Anyone may view an approved article/newsletter; otherwise
            # only the owning journalist may view their own pending item.
            return getattr(obj, "approved", True) or is_owner
        if user.role == "JOURNALIST":
            return is_owner
        return False


class IsEditor(permissions.BasePermission):
    """Used for the approve action."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.role == "EDITOR"))


class ReadOnlyForReaders(permissions.BasePermission):
    """Readers (and anyone without an explicit write permission) get GET/HEAD/OPTIONS only."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in ("EDITOR", "JOURNALIST")
        )
