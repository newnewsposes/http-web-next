#!/bin/bash
# Fix PostgreSQL authentication for ThisIsCloud

set -e

echo "🔧 PostgreSQL Authentication Fix"
echo "================================="

# Check if PostgreSQL is running
if ! sudo systemctl is-active --quiet postgresql; then
    echo "❌ PostgreSQL is not running. Starting it..."
    sudo systemctl start postgresql
fi

echo ""
echo "Current database setup:"
sudo -u postgres psql -c "\l" | grep filehosting || echo "❌ Database 'filehosting' not found"
sudo -u postgres psql -c "\du" | grep fileuser || echo "❌ User 'fileuser' not found"

echo ""
echo "Choose an option:"
echo "1) Reset database password (recommended)"
echo "2) Recreate database and user from scratch"
echo "3) Show current DATABASE_URL from systemd service"
read -p "Enter choice [1]: " CHOICE
CHOICE=${CHOICE:-1}

if [ "$CHOICE" = "1" ]; then
    echo ""
    read -s -p "Enter NEW password for fileuser: " NEW_PASS
    echo
    
    # Update PostgreSQL password
    sudo -u postgres psql -c "ALTER USER fileuser WITH PASSWORD '$NEW_PASS';"
    echo "✅ Password updated in PostgreSQL"
    
    echo ""
    echo "Now update your systemd service with the new password:"
    echo "sudo systemctl edit --full ThisIsCloud.service"
    echo ""
    echo "Change the DATABASE_URL line to:"
    echo "Environment=\"DATABASE_URL=postgresql://fileuser:$NEW_PASS@localhost/filehosting\""
    echo ""
    echo "Then run:"
    echo "sudo systemctl daemon-reload"
    echo "sudo systemctl restart ThisIsCloud"
    
elif [ "$CHOICE" = "2" ]; then
    echo ""
    read -s -p "Enter password for fileuser: " DB_PASSWORD
    echo
    
    # Drop and recreate
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS filehosting;" 
    sudo -u postgres psql -c "DROP USER IF EXISTS fileuser;"
    sudo -u postgres psql -c "CREATE DATABASE filehosting;"
    sudo -u postgres psql -c "CREATE USER fileuser WITH PASSWORD '$DB_PASSWORD';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE filehosting TO fileuser;"
    
    echo "✅ Database and user recreated"
    echo ""
    echo "Update DATABASE_URL in systemd service (see option 1 instructions above)"
    
elif [ "$CHOICE" = "3" ]; then
    echo ""
    sudo systemctl cat ThisIsCloud.service | grep DATABASE_URL || echo "❌ No DATABASE_URL found in service"
fi

echo ""
echo "🧪 Test connection manually:"
echo "PGPASSWORD='your_password' psql -h localhost -U fileuser -d filehosting -c 'SELECT 1;'"
