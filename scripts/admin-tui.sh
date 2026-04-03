#!/bin/bash
# Admin Management TUI for ThisIsCloud
# Interactive terminal UI for managing users and admins

set -e

# Get the directory where this script lives
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MANAGE_SCRIPT="$SCRIPT_DIR/manage_admins.py"

# Check if dialog is installed, fallback to whiptail
if command -v dialog &> /dev/null; then
    DIALOG=dialog
elif command -v whiptail &> /dev/null; then
    DIALOG=whiptail
else
    echo "❌ Neither dialog nor whiptail found. Installing dialog..."
    sudo apt-get update && sudo apt-get install -y dialog
    DIALOG=dialog
fi

# Ensure we're in the venv
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -f "$PROJECT_ROOT/venv/bin/activate" ]; then
        source "$PROJECT_ROOT/venv/bin/activate"
    else
        echo "❌ Virtual environment not found at $PROJECT_ROOT/venv"
        exit 1
    fi
fi

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function to show message boxes
show_message() {
    local title="$1"
    local message="$2"
    $DIALOG --title "$title" --msgbox "$message" 10 60
}

show_error() {
    $DIALOG --title "Error" --msgbox "$1" 8 60
}

show_success() {
    $DIALOG --title "Success" --msgbox "$1" 8 60
}

# Get user list for selection menus
get_user_list() {
    python3 << 'PYEOF'
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from app import create_app, db
from app.models.user import User

app = create_app()
with app.app_context():
    users = User.query.order_by(User.username).all()
    for u in users:
        admin_badge = " [ADMIN]" if u.is_admin else ""
        active_badge = " [DISABLED]" if not u.is_active else ""
        print(f"{u.username} \"{u.email}{admin_badge}{active_badge}\"")
PYEOF
}

# Main menu
main_menu() {
    while true; do
        choice=$($DIALOG --title "ThisIsCloud Admin Management" \
            --menu "Choose an operation:" 20 70 12 \
            "1" "List all users" \
            "2" "List admins only" \
            "3" "View user details" \
            "4" "Add new user" \
            "5" "Add new admin" \
            "6" "Promote user to admin" \
            "7" "Demote admin to user" \
            "8" "Reset user password" \
            "9" "Set storage quota" \
            "10" "Enable/Disable account" \
            "11" "Delete user" \
            "12" "Exit" \
            3>&1 1>&2 2>&3)
        
        case $choice in
            1) list_users ;;
            2) list_admins ;;
            3) view_user_info ;;
            4) add_user false ;;
            5) add_user true ;;
            6) promote_user ;;
            7) demote_user ;;
            8) reset_password ;;
            9) set_quota ;;
            10) toggle_active ;;
            11) delete_user ;;
            12) clear; exit 0 ;;
            *) exit 0 ;;
        esac
    done
}

list_users() {
    OUTPUT=$(cd "$PROJECT_ROOT" && python3 "$MANAGE_SCRIPT" list 2>&1)
    $DIALOG --title "All Users" --msgbox "$OUTPUT" 25 110
}

list_admins() {
    OUTPUT=$(cd "$PROJECT_ROOT" && python3 "$MANAGE_SCRIPT" list --admins-only 2>&1)
    $DIALOG --title "Admin Users" --msgbox "$OUTPUT" 20 110
}

view_user_info() {
    USERS=$(get_user_list)
    if [ -z "$USERS" ]; then
        show_error "No users found"
        return
    fi
    
    USERNAME=$($DIALOG --title "Select User" --menu "Choose a user to view:" 20 70 12 $USERS 3>&1 1>&2 2>&3)
    
    if [ -n "$USERNAME" ]; then
        OUTPUT=$(cd "$PROJECT_ROOT" && python3 "$MANAGE_SCRIPT" info --username "$USERNAME" 2>&1)
        $DIALOG --title "User Info: $USERNAME" --msgbox "$OUTPUT" 20 60
    fi
}

add_user() {
    local is_admin=$1
    local title="Add New User"
    [ "$is_admin" = true ] && title="Add New Admin"
    
    # Get username
    USERNAME=$($DIALOG --title "$title" --inputbox "Enter username:" 8 60 3>&1 1>&2 2>&3)
    [ -z "$USERNAME" ] && return
    
    # Get email
    EMAIL=$($DIALOG --title "$title" --inputbox "Enter email:" 8 60 3>&1 1>&2 2>&3)
    [ -z "$EMAIL" ] && return
    
    # Get password
    PASSWORD=$($DIALOG --title "$title" --passwordbox "Enter password:" 8 60 3>&1 1>&2 2>&3)
    [ -z "$PASSWORD" ] && return
    
    # Confirm password
    PASSWORD2=$($DIALOG --title "$title" --passwordbox "Confirm password:" 8 60 3>&1 1>&2 2>&3)
    if [ "$PASSWORD" != "$PASSWORD2" ]; then
        show_error "Passwords do not match!"
        return
    fi
    
    # Execute
    if [ "$is_admin" = true ]; then
        OUTPUT=$(cd "$PROJECT_ROOT" && python3 "$MANAGE_SCRIPT" add --username "$USERNAME" --email "$EMAIL" --password "$PASSWORD" --admin 2>&1)
    else
        OUTPUT=$(cd "$PROJECT_ROOT" && python3 "$MANAGE_SCRIPT" add --username "$USERNAME" --email "$EMAIL" --password "$PASSWORD" 2>&1)
    fi
    
    if echo "$OUTPUT" | grep -q "✅"; then
        show_success "$OUTPUT"
    else
        show_error "$OUTPUT"
    fi
}

promote_user() {
    USERS=$(get_user_list)
    if [ -z "$USERS" ]; then
        show_error "No users found"
        return
    fi
    
    USERNAME=$($DIALOG --title "Promote to Admin" --menu "Choose user to promote:" 20 70 12 $USERS 3>&1 1>&2 2>&3)
    
    if [ -n "$USERNAME" ]; then
        OUTPUT=$(cd "$PROJECT_ROOT" && python3 "$MANAGE_SCRIPT" promote --username "$USERNAME" 2>&1)
        if echo "$OUTPUT" | grep -q "✅"; then
            show_success "$OUTPUT"
        else
            show_error "$OUTPUT"
        fi
    fi
}

demote_user() {
    USERS=$(get_user_list)
    if [ -z "$USERS" ]; then
        show_error "No users found"
        return
    fi
    
    USERNAME=$($DIALOG --title "Demote from Admin" --menu "Choose admin to demote:" 20 70 12 $USERS 3>&1 1>&2 2>&3)
    
    if [ -n "$USERNAME" ]; then
        if $DIALOG --title "Confirm" --yesno "Demote $USERNAME from admin?" 8 60; then
            OUTPUT=$(cd "$PROJECT_ROOT" && python3 "$MANAGE_SCRIPT" demote --username "$USERNAME" 2>&1)
            if echo "$OUTPUT" | grep -q "✅"; then
                show_success "$OUTPUT"
            else
                show_error "$OUTPUT"
            fi
        fi
    fi
}

reset_password() {
    USERS=$(get_user_list)
    if [ -z "$USERS" ]; then
        show_error "No users found"
        return
    fi
    
    USERNAME=$($DIALOG --title "Reset Password" --menu "Choose user:" 20 70 12 $USERS 3>&1 1>&2 2>&3)
    
    if [ -n "$USERNAME" ]; then
        PASSWORD=$($DIALOG --title "Reset Password" --passwordbox "Enter new password for $USERNAME:" 8 60 3>&1 1>&2 2>&3)
        [ -z "$PASSWORD" ] && return
        
        PASSWORD2=$($DIALOG --title "Reset Password" --passwordbox "Confirm new password:" 8 60 3>&1 1>&2 2>&3)
        if [ "$PASSWORD" != "$PASSWORD2" ]; then
            show_error "Passwords do not match!"
            return
        fi
        
        OUTPUT=$(cd "$PROJECT_ROOT" && python3 "$MANAGE_SCRIPT" reset-password --username "$USERNAME" --password "$PASSWORD" 2>&1)
        if echo "$OUTPUT" | grep -q "✅"; then
            show_success "$OUTPUT"
        else
            show_error "$OUTPUT"
        fi
    fi
}

set_quota() {
    USERS=$(get_user_list)
    if [ -z "$USERS" ]; then
        show_error "No users found"
        return
    fi
    
    USERNAME=$($DIALOG --title "Set Storage Quota" --menu "Choose user:" 20 70 12 $USERS 3>&1 1>&2 2>&3)
    
    if [ -n "$USERNAME" ]; then
        QUOTA=$($DIALOG --title "Set Storage Quota" --inputbox "Enter quota in GB (0 for unlimited):" 8 60 "10" 3>&1 1>&2 2>&3)
        
        if [ -n "$QUOTA" ]; then
            OUTPUT=$(cd "$PROJECT_ROOT" && python3 "$MANAGE_SCRIPT" set-quota --username "$USERNAME" --quota "$QUOTA" 2>&1)
            if echo "$OUTPUT" | grep -q "✅"; then
                show_success "$OUTPUT"
            else
                show_error "$OUTPUT"
            fi
        fi
    fi
}

toggle_active() {
    USERS=$(get_user_list)
    if [ -z "$USERS" ]; then
        show_error "No users found"
        return
    fi
    
    USERNAME=$($DIALOG --title "Enable/Disable Account" --menu "Choose user:" 20 70 12 $USERS 3>&1 1>&2 2>&3)
    
    if [ -n "$USERNAME" ]; then
        OUTPUT=$(cd "$PROJECT_ROOT" && python3 "$MANAGE_SCRIPT" toggle-active --username "$USERNAME" 2>&1)
        if echo "$OUTPUT" | grep -q "✅" || echo "$OUTPUT" | grep -q "🔒"; then
            show_success "$OUTPUT"
        else
            show_error "$OUTPUT"
        fi
    fi
}

delete_user() {
    USERS=$(get_user_list)
    if [ -z "$USERS" ]; then
        show_error "No users found"
        return
    fi
    
    USERNAME=$($DIALOG --title "Delete User" --menu "Choose user to DELETE:" 20 70 12 $USERS 3>&1 1>&2 2>&3)
    
    if [ -n "$USERNAME" ]; then
        if $DIALOG --title "⚠️  CONFIRM DELETION" --yesno "Are you sure you want to DELETE user '$USERNAME'?\n\nThis will remove their account and ALL their files!" 12 60; then
            OUTPUT=$(cd "$PROJECT_ROOT" && python3 "$MANAGE_SCRIPT" remove --username "$USERNAME" --force 2>&1)
            if echo "$OUTPUT" | grep -q "✅"; then
                show_success "$OUTPUT"
            else
                show_error "$OUTPUT"
            fi
        fi
    fi
}

# Check if running from correct location
if [ ! -f "$MANAGE_SCRIPT" ]; then
    echo "❌ Error: manage_admins.py not found at $MANAGE_SCRIPT"
    echo "Please run this script from the project root or scripts directory"
    exit 1
fi

# Start the TUI
clear
main_menu
