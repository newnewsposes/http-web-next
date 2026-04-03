#!/usr/bin/env python3
"""
manage_admins.py — simple admin user management script for ThisIsCloud

Usage:
  ./scripts/manage_admins.py add --username USER --email EMAIL --password PASS
  ./scripts/manage_admins.py promote --username USER
  ./scripts/manage_admins.py demote --username USER
  ./scripts/manage_admins.py remove --username USER
  ./scripts/manage_admins.py toggle-active --username USER
  ./scripts/manage_admins.py list

This script runs in the app context and modifies the database accordingly.
"""
import argparse
import sys
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
    with app.app_context():
        if User.query.filter_by(username=username).first():
            print(f"User '{username}' already exists")
            return
        if User.query.filter_by(email=email).first():
            print(f"Email '{email}' already registered")
            return
        user = User(username=username, email=email, is_admin=is_admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Created user: {username} (admin={is_admin})")


def promote_user(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"User '{username}' not found")
            return
        user.is_admin = True
        db.session.commit()
        print(f"Promoted {username} to admin")


def demote_user(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"User '{username}' not found")
            return
        if user.username == 'admin':
            print('Refusing to demote root admin named "admin"')
            return
        user.is_admin = False
        db.session.commit()
        print(f"Revoked admin from {username}")


def remove_user(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"User '{username}' not found")
            return
        db.session.delete(user)
        db.session.commit()
        print(f"Deleted user {username}")


def toggle_active(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"User '{username}' not found")
            return
        user.is_active = not user.is_active
        db.session.commit()
        print(f"Set {username}.is_active = {user.is_active}")


def list_users():
    with app.app_context():
        users = User.query.order_by(User.created_at.desc()).all()
        print(f"{'username':20} {'email':30} {'admin':5} {'active':6} {'quota(GB)':>10}")
        print('-'*80)
        for u in users:
            quota = 'unlimited' if u.storage_quota is None else f"{u.storage_quota/1024/1024/1024:.2f}"
            print(f"{u.username:20} {u.email:30} {str(u.is_admin):5} {str(u.is_active):6} {quota:>10}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='manage_admins.py')
    sub = parser.add_subparsers(dest='cmd')

    p_add = sub.add_parser('add')
    p_add.add_argument('--username', required=True)
    p_add.add_argument('--email', required=True)
    p_add.add_argument('--password', required=True)
    p_add.add_argument('--admin', action='store_true')

    p_prom = sub.add_parser('promote')
    p_prom.add_argument('--username', required=True)

    p_dem = sub.add_parser('demote')
    p_dem.add_argument('--username', required=True)

    p_rem = sub.add_parser('remove')
    p_rem.add_argument('--username', required=True)

    p_toggle = sub.add_parser('toggle-active')
    p_toggle.add_argument('--username', required=True)

    p_list = sub.add_parser('list')

    args = parser.parse_args()

    if args.cmd == 'add':
        add_user(args.username, args.email, args.password, is_admin=args.admin)
    elif args.cmd == 'promote':
        promote_user(args.username)
    elif args.cmd == 'demote':
        demote_user(args.username)
    elif args.cmd == 'remove':
        remove_user(args.username)
    elif args.cmd == 'toggle-active':
        toggle_active(args.username)
    elif args.cmd == 'list':
        list_users()
    else:
        parser.print_help()
