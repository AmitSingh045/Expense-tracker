from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

class Command(BaseCommand):
    help = "Sets up standard group roles and permission matrices for the finance system."

    def handle(self, *args, **options):
        self.stdout.write("Configuring role-based user groups...")

        # 1. Define groups
        groups_config = {
            'Manager': {
                'models': ['transaction', 'category', 'paymentmethod', 'currency', 'budget', 'goal', 'bill', 'notification', 'report', 'profile'],
                'actions': ['view', 'add', 'change', 'delete']
            },
            'Staff': {
                'models': ['transaction', 'category', 'budget', 'goal', 'bill', 'notification'],
                'actions': ['view', 'add', 'change']
            },
            'Read-Only Auditor': {
                'models': ['transaction', 'category', 'paymentmethod', 'currency', 'budget', 'goal', 'bill', 'notification', 'report', 'profile', 'activitylog', 'auditlog', 'user'],
                'actions': ['view']
            }
        }

        for group_name, config in groups_config.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f"Created group: {group_name}")
            
            # Clear existing permissions to prevent duplicates on rerun
            group.permissions.clear()
            
            # Assign permissions
            perms_to_add = []
            for model_name in config['models']:
                try:
                    # Find content type for this model
                    ct = ContentType.objects.filter(model=model_name).first()
                    if not ct:
                        self.stdout.write(self.style.WARNING(f"Content Type for model '{model_name}' not found. Skipping."))
                        continue

                    for act in config['actions']:
                        codename = f"{act}_{model_name}"
                        perm = Permission.objects.filter(content_type=ct, codename=codename).first()
                        if perm:
                            perms_to_add.append(perm)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error resolving permissions for {model_name}: {str(e)}"))

            if perms_to_add:
                group.permissions.add(*perms_to_add)
                self.stdout.write(f"Assigned {len(perms_to_add)} permissions to {group_name}.")

        self.stdout.write(self.style.SUCCESS("Group roles and permissions configured successfully!"))
