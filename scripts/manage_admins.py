#!/usr/bin/env python3
"""
manage_admins.py — Admin user management script for ThisIsCloud

Usage:
  ./scripts/manage_admins.py add --username USER --email EMAIL --password PASS [--admin]
  ./scripts/manage_admins.py promote --username USER
  ./scripts/manage_admins.py demote --username USER
  ./scripts/manage_admins.py remove --username USER [--force]
  ./scripts/manage_admins.py toggle-active --username USER
  ./scripts/manage_admins.py reset-password --username USER --password NEWPASS
  ./scripts/manage_admins.py set-quota --username USER --quota GB
  ./scripts/manage_admins.py list [--admins-only]
  ./scripts/manage_admins.py info --username USER

This script runs in the app context and modifies the database directly.
"""
import argparse
import sys
import getpass
from pathlib import Path

# Ensure project root is on sys.path so 'app' package can be imported when running
# this script from any working directory.
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app, db
from app.models.user import User

app = create_app()


def add_user(username, email, password, is_admin=False):
    """Create a new user."""
    with app.app_context():
        if User.query.filter_by(username=username).first():
            print(f"❌ User '{username}' already exists")
            return False
        if User.query.filter_by(email=email).first():
            print(f"❌ Email '{email}' already registered")
            return False
        
        user = User(username=username, email=email, is_admin=is_admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        role = "admin" if is_admin else "user"
        print(f"✅ Created {role}: {username} ({email})")
        return True


def promote_user(username):
    """Promote a user to admin."""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ User '{username}' not found")
            return False
        
        if user.is_admin:
            print(f"ℹ️  {username} is already an admin")
            return True
        
        user.is_admin = True
        db.session.commit()
        print(f"✅ Promoted {username} to admin")
        return True


def demote_user(username):
    """Revoke admin privileges from a user."""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ User '{username}' not found")
            return False
        
        if not user.is_admin:
            print(f"ℹ️  {username} is not an admin")
            return True
        
        # Count remaining admins
        admin_count = User.query.filter_by(is_admin=True).count()
        if admin_count <= 1:
            print(f"❌ Cannot demote {username} - must have at least one admin")
            return False
        
        user.is_admin = False
        db.session.commit()
        print(f"✅ Revoked admin from {username}")
        return True


def remove_user(username, force=False):
    """Delete a user and their files."""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ User '{username}' not found")
            return False
        
        # Prevent accidental admin deletion
        if user.is_admin and not force:
            print(f"❌ {username} is an admin. Use --force to confirm deletion")
            return False
        
        file_count = len(user.files)
        if file_count > 0 and not force:
            print(f"❌ {username} has {file_count} files. Use --force to delete user and all their files")
            return False
        
        # Delete user's files
        if file_count > 0:
            import os
            from flask import current_app
            for file in user.files:
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
            print(f"🗑️  Deleted {file_count} files")
        
        db.session.delete(user)
        db.session.commit()
        print(f"✅ Deleted user {username}")
        return True


def toggle_active(username):
    """Enable or disable a user account."""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ User '{username}' not found")
            return False
        
        user.is_active = not user.is_active
        db.session.commit()
        
        status = "enabled" if user.is_active else "disabled"
        icon = "✅" if user.is_active else "🔒"
        print(f"{icon} {username} account {status}")
        return True


def reset_password(username, password):
    """Reset a user's password."""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ User '{username}' not found")
            return False
        
        user.set_password(password)
        db.session.commit()
        print(f"✅ Password reset for {username}")
        return True


def set_quota(username, quota_gb):
    """Set storage quota for a user (in GB)."""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ User '{username}' not found")
            return False
        
        if quota_gb == 0:
            user.storage_quota = None
            print(f"✅ Set unlimited quota for {username}")
        else:
            quota_bytes = int(quota_gb * 1024 * 1024 * 1024)
            user.storage_quota = quota_bytes
            print(f"✅ Set {quota_gb} GB quota for {username}")
        
        db.session.commit()
        return True


def user_info(username):
    """Display detailed information about a user."""
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"❌ User '{username}' not found")
            return False
        
        quota = 'unlimited' if user.storage_quota is None else f"{user.storage_quota/1024/1024/1024:.2f} GB"
        used = user.get_storage_used() / 1024 / 1024 / 1024
        
        print(f"\n👤 User Information")
        print(f"{'─'*50}")
        print(f"Username:      {user.username}")
        print(f"Email:         {user.email}")
        print(f"Admin:         {'Yes ⭐' if user.is_admin else 'No'}")
        print(f"Active:        {'Yes ✅' if user.is_active else 'No 🔒'}")
        print(f"Created:       {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Storage Used:  {used:.2f} GB")
        print(f"Storage Quota: {quota}")
        print(f"Files:         {len(user.files)}")
        print(f"{'─'*50}\n")
        return True


def list_users(admins_only=False):
    """List all users or just admins."""
    with app.app_context():
        query = User.query
        if admins_only:
            query = query.filter_by(is_admin=True)
        
        users = query.order_by(User.created_at.desc()).all()
        
        title = "Admin Users" if admins_only else "All Users"
        print(f"\n{title}")
        print(f"{'─'*100}")
        print(f"{'Username':20} {'Email':30} {'Admin':6} {'Active':7} {'Files':>6} {'Quota':>12}")
        print(f"{'─'*100}")
        
        for u in users:
            quota = 'unlimited' if u.storage_quota is None else f"{u.storage_quota/1024/1024/1024:.1f} GB"
            admin_icon = '⭐' if u.is_admin else ''
            active_icon = '✅' if u.is_active else '🔒'
            
            print(f"{u.username:20} {u.email:30} {admin_icon:6} {active_icon:7} {len(u.files):>6} {quota:>12}")
        
        print(f"{'─'*100}")
        print(f"Total: {len(users)} user(s)\n")
        return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='manage_admins.py',
        description='Manage ThisIsCloud users and admins',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest='cmd', help='Command to execute')

    # Add user
    p_add = sub.add_parser('add', help='Create a new user')
    p_add.add_argument('--username', required=True, help='Username')
    p_add.add_argument('--email', required=True, help='Email address')
    p_add.add_argument('--password', help='Password (will prompt if not provided)')
    p_add.add_argument('--admin', action='store_true', help='Create as admin')

    # Promote to admin
    p_prom = sub.add_parser('promote', help='Promote user to admin')
    p_prom.add_argument('--username', required=True, help='Username to promote')

    # Demote from admin
    p_dem = sub.add_parser('demote', help='Revoke admin privileges')
    p_dem.add_argument('--username', required=True, help='Username to demote')

    # Remove user
    p_rem = sub.add_parser('remove', help='Delete a user')
    p_rem.add_argument('--username', required=True, help='Username to delete')
    p_rem.add_argument('--force', action='store_true', help='Force deletion (for admins or users with files)')

    # Toggle active status
    p_toggle = sub.add_parser('toggle-active', help='Enable/disable user account')
    p_toggle.add_argument('--username', required=True, help='Username to toggle')

    # Reset password
    p_reset = sub.add_parser('reset-password', help='Reset user password')
    p_reset.add_argument('--username', required=True, help='Username')
    p_reset.add_argument('--password', help='New password (will prompt if not provided)')

    # Set quota
    p_quota = sub.add_parser('set-quota', help='Set storage quota for user')
    p_quota.add_argument('--username', required=True, help='Username')
    p_quota.add_argument('--quota', type=float, required=True, help='Quota in GB (0 for unlimited)')

    # User info
    p_info = sub.add_parser('info', help='Display detailed user information')
    p_info.add_argument('--username', required=True, help='Username to query')

    # List users
    p_list = sub.add_parser('list', help='List users')
    p_list.add_argument('--admins-only', action='store_true', help='Show only admins')

    args = parser.parse_args()

    if args.cmd == 'add':
        password = args.password or getpass.getpass('Password: ')
        if not password:
            print("❌ Password cannot be empty")
            sys.exit(1)
        add_user(args.username, args.email, password, is_admin=args.admin)
    
    elif args.cmd == 'promote':
        promote_user(args.username)
    
    elif args.cmd == 'demote':
        demote_user(args.username)
    
    elif args.cmd == 'remove':
        remove_user(args.username, force=args.force)
    
    elif args.cmd == 'toggle-active':
        toggle_active(args.username)
    
    elif args.cmd == 'reset-password':
        password = args.password or getpass.getpass('New password: ')
        if not password:
            print("❌ Password cannot be empty")
            sys.exit(1)
        reset_password(args.username, password)
    
    elif args.cmd == 'set-quota':
        set_quota(args.username, args.quota)
    
    elif args.cmd == 'info':
        user_info(args.username)
    
    elif args.cmd == 'list':
        list_users(admins_only=args.admins_only)
    
    else:
        parser.print_help()
