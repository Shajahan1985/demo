# Generated migration for creating default roles

from django.db import migrations
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


def create_default_roles(apps, schema_editor):
    """
    Create default roles (groups) with appropriate permissions.
    
    Default roles:
    1. Admin - Full access to user and role management
    2. Manager - Can view users and manage assets (when asset app is added)
    3. User - Basic access to view and manage own assets
    """
    
    # Get models
    User = apps.get_model('auth', 'User')
    Group_model = apps.get_model('auth', 'Group')
    Permission_model = apps.get_model('auth', 'Permission')
    ContentType_model = apps.get_model('contenttypes', 'ContentType')
    
    # Get content types
    user_content_type = ContentType_model.objects.get_for_model(User)
    group_content_type = ContentType_model.objects.get_for_model(Group_model)
    
    # Define roles and their permissions (codename, content_type_id)
    roles_config = {
        'Admin': {
            'description': 'Full administrative access',
            'permissions': [
                # User permissions
                ('add_user', user_content_type.id),
                ('change_user', user_content_type.id),
                ('delete_user', user_content_type.id),
                ('view_user', user_content_type.id),
                # Group permissions
                ('add_group', group_content_type.id),
                ('change_group', group_content_type.id),
                ('delete_group', group_content_type.id),
                ('view_group', group_content_type.id),
            ]
        },
        'Manager': {
            'description': 'Can view users and manage assets',
            'permissions': [
                # User permissions (view only)
                ('view_user', user_content_type.id),
                ('view_group', group_content_type.id),
            ]
        },
        'User': {
            'description': 'Basic user access',
            'permissions': [
                # Basic permissions - can be extended when asset app is added
            ]
        }
    }
    
    # Create roles and assign permissions
    for role_name, role_config in roles_config.items():
        # Create or get the group
        group, created = Group_model.objects.get_or_create(name=role_name)
        
        if created:
            print(f"Created role: {role_name}")
        else:
            print(f"Role already exists: {role_name}")
        
        # Clear existing permissions
        group.permissions.clear()
        
        # Add permissions to the group
        for perm_codename, content_type_id in role_config['permissions']:
            try:
                permission = Permission_model.objects.get(
                    codename=perm_codename,
                    content_type_id=content_type_id
                )
                group.permissions.add(permission)
                print(f"  Added permission: {perm_codename}")
            except Permission_model.DoesNotExist:
                print(f"  Warning: Permission {perm_codename} not found")


def remove_default_roles(apps, schema_editor):
    """
    Remove default roles created by this migration.
    """
    Group = apps.get_model('auth', 'Group')
    
    role_names = ['Admin', 'Manager', 'User']
    
    for role_name in role_names:
        try:
            group = Group.objects.get(name=role_name)
            group.delete()
            print(f"Removed role: {role_name}")
        except Group.DoesNotExist:
            print(f"Role not found: {role_name}")


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '__first__'),
        ('auth', '__first__'),
        ('contenttypes', '__first__'),
    ]

    operations = [
        migrations.RunPython(create_default_roles, remove_default_roles),
    ]
