import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q
from django.db import transaction
from settings.models import SystemDay
from users.models import Permission, PermissionCategory 
from approval.models import Action
from institution.models import (
    BranchWorkingDays,
    Institution,
    Branch,
    InstitutionWorkingDays,
)

class Command(BaseCommand):
    help = "Add/sync permissions, systems, discipline types, approval actions, system days, bank info, awards, birthday events, performance data, resend welcome emails, sync employee names, and delete inactive employees"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset-password",
            action="store_true",
            help="Reset passwords for all resent welcome emails",
        )
        parser.add_argument(
            "--employee-ids",
            type=str,
            help="Comma-separated list of employee IDs to resend welcome emails to",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting inactive employees",
        )
        parser.add_argument(
            "--no-confirm",
            action="store_true",
            help="Skip confirmation prompt for deleting inactive employees",
        )

    def handle(self, *args, **kwargs):
        self.sync_permissions()
        self.sync_approval_actions()
        self.create_default_working_days()



    def sync_permissions(self):
        filepath = os.path.join(settings.BASE_DIR, "users", "fixtures", "permissions.json")
        if not os.path.exists(filepath):
            self.stdout.write(self.style.ERROR(f"Permissions file not found at {filepath}"))
            return
        with open(filepath, "r") as file:
            permissions_data = json.load(file)
        self.stdout.write(self.style.MIGRATE_HEADING("⏳ Syncing permissions...\n"))
        valid_permission_codes = set()
        valid_category_names = set()
        for category_name, perms in permissions_data.items():
            category, _ = PermissionCategory.objects.get_or_create(
                permission_category_name=category_name,
                defaults={"permission_category_description": f"{category_name} related permissions"},
            )
            valid_category_names.add(category.permission_category_name)
            for perm in perms:
                Permission.objects.update_or_create(
                    permission_code=perm["code"],
                    defaults={
                        "permission_name": perm["name"],
                        "permission_description": perm["description"],
                        "category": category,
                    },
                )
                valid_permission_codes.add(perm["code"])
        deleted_permissions, _ = Permission.objects.exclude(
            permission_code__in=valid_permission_codes
        ).delete()
        deleted_categories, _ = PermissionCategory.objects.exclude(
            permission_category_name__in=valid_category_names
        ).delete()
        self.stdout.write("\n" + self.style.MIGRATE_LABEL("📋 Permissions Summary"))
        self.stdout.write(self.style.NOTICE(f"  🧹 Removed Permissions: {deleted_permissions}"))
        self.stdout.write(self.style.NOTICE(f"  🧹 Removed Categories: {deleted_categories}"))
        self.stdout.write(self.style.SUCCESS("\n🎉 Permissions synced successfully!"))



    def sync_approval_actions(self):
        self.stdout.write(self.style.MIGRATE_HEADING("\n⏳ Syncing approval actions...\n"))
        default_actions = [
            {
                "name": "create",
                "description": "Action for creating new records that require approval",
            },
            {
                "name": "update",
                "description": "Action for updating existing records that require approval",
            },
            {
                "name": "delete",
                "description": "Action for deleting records that require approval",
            },
        ]
        valid_action_names = set()
        created_count = 0
        updated_count = 0
        for action_data in default_actions:
            action, created = Action.objects.update_or_create(
                name=action_data["name"],
                defaults={"description": action_data["description"]},
            )
            valid_action_names.add(action_data["name"])
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✅ Created approval action: {action.name} (Code: {action.code})"))
            else:
                updated_count += 1
                self.stdout.write(self.style.NOTICE(f"  ♻️ Updated approval action: {action.name} (Code: {action.code})"))
        self.stdout.write("\n" + self.style.MIGRATE_LABEL("📋 Approval Actions Summary"))
        self.stdout.write(self.style.NOTICE(f"  ➕ Created: {created_count}"))
        self.stdout.write(self.style.NOTICE(f"  ♻️ Updated: {updated_count}"))
        self.stdout.write(self.style.SUCCESS("\n🎉 Approval actions synced successfully!"))

    def create_default_working_days(self):
        institutions = Institution.objects.all()
        for institution in institutions:
            self.stdout.write(f"Processing {institution.institution_name}")
            
            # First, create InstitutionWorkingDays for the institution
            self.stdout.write(f"\nProcessing Working Days for {institution.institution_name}")
            try:
                working_days, created = InstitutionWorkingDays.objects.get_or_create(institution=institution)
                if created:
                    # Ensure SystemDay objects exist
                    system_days = SystemDay.objects.all()
                    if system_days.exists():
                        working_days.days.set(system_days)
                        self.stdout.write(self.style.SUCCESS(f"   └─ Created default working days for {institution.institution_name}"))
                    else:
                        self.stdout.write(self.style.ERROR(f"   └─ No SystemDay objects found! Cannot set working days for {institution.institution_name}"))
                else:
                    self.stdout.write(self.style.NOTICE(f"   └─ Default working days already exist for {institution.institution_name}"))

                # Then, create BranchWorkingDays for each branch
                branches = Branch.objects.filter(institution=institution)
                for branch in branches:
                    try:
                        branch_working_days, created = BranchWorkingDays.objects.get_or_create(branch=branch)
                        if created:
                            self.stdout.write(self.style.SUCCESS(f"    └─ Created working days for branch '{branch.branch_name or branch.branch_location}'"))
                        else:
                            self.stdout.write(self.style.NOTICE(f"    └─ Branch '{branch.branch_name or branch.branch_location}' already has working days"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"    └─ Error creating working days for branch '{branch.branch_name or branch.branch_location}': {str(e)}"))
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   └─ Error processing institution {institution.institution_name}: {str(e)}"))


