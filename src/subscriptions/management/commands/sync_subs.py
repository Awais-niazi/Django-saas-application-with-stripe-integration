from typing import Any
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from subscriptions.models import Subscriptions


class Command(BaseCommand):
    help = (
        "Synchronize subscription permissions with groups.\n"
        "Usage:\n"
        "  python manage.py sync_subs                   # Normal sync (non-destructive)\n"
        "  python manage.py sync_subs --overwrite       # Reset all group permissions to subscription defaults\n"
        "  python manage.py sync_subs --sync-from-groups # Make current group permissions the new defaults"
    )

    def add_arguments(self, parser):
        parser.add_argument("--overwrite", action="store_true", help="Reset all group permissions.")
        parser.add_argument("--sync-from-groups", action="store_true", help="Update defaults from group permissions.")

    def handle(self, *args: Any, **options: Any):
        overwrite = options.get("overwrite")
        sync_from_groups = options.get("sync_from_groups")

        qs = Subscriptions.objects.all()  # <- changed

        if not qs.exists():
            self.stdout.write(self.style.WARNING("No subscriptions found."))
            return

        if overwrite and sync_from_groups:
            self.stdout.write(self.style.ERROR("Cannot use --overwrite and --sync-from-groups together."))
            return

        if sync_from_groups:
            self.sync_from_groups(qs)
        else:
            self.sync_to_groups(qs, overwrite)

    def sync_to_groups(self, qs, overwrite=False):
        for obj in qs:
            sub_perms = obj.permissions.all()
            for group in obj.groups.all():
                if overwrite:
                    group.permissions.set(sub_perms)
                    self.stdout.write(
                        self.style.SUCCESS(f"[OVERWRITE] Reset {group.name} permissions to match {obj.name}.")
                    )
                else:
                    current = group.permissions.all()
                    missing = sub_perms.difference(current)
                    if missing.exists():
                        group.permissions.add(*missing)
                        self.stdout.write(
                            self.style.SUCCESS(f"[SYNC] Added {missing.count()} missing perms to {group.name}.")
                        )
                    else:
                        self.stdout.write(self.style.NOTICE(f"[OK] {group.name} already in sync."))

    def sync_from_groups(self, qs):
        for obj in qs:
            all_group_perms = Permission.objects.filter(group__in=obj.groups.all()).distinct()
            obj.permissions.set(all_group_perms)
            self.stdout.write(
                self.style.SUCCESS(f"[SYNC-FROM-GROUPS] Updated {obj.name} defaults from current groups.")
            )
