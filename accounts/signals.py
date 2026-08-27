"""
Signals that keep a CustomUser's group membership and role-specific
fields consistent with their `role` field.
"""
from django.contrib.auth.models import Group
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from .models import CustomUser, Role


@receiver(post_save, sender=CustomUser)
def sync_user_group_and_fields(sender, instance, created, **kwargs):
    """
    1. Add the user to the Group matching their role (removing them from
       the other role groups first, so a role change moves them cleanly).
    2. Enforce "journalist fields are None for readers, and vice versa"
       by clearing the reader-only subscription M2M fields whenever the
       user is NOT a reader.
    """
    role_group_names = [Role.READER.label, Role.EDITOR.label, Role.JOURNALIST.label]
    target_group_name = instance.get_role_display()

    # Make sure all three groups exist (safety net if setup_groups was not run)
    groups = {}
    for name in role_group_names:
        group, _ = Group.objects.get_or_create(name=name)
        groups[name] = group

    # Remove from any role group that no longer matches, add to the correct one
    for name, group in groups.items():
        if name == target_group_name:
            instance.groups.add(group)
        else:
            instance.groups.remove(group)

    # Reader-only fields must be empty ("None") unless the user is a Reader.
    if instance.role != Role.READER:
        instance.subscriptions_publishers.clear()
        instance.subscriptions_journalists.clear()
