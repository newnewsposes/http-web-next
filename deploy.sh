#!/bin/bash
# Complete deployment script for ThisIsCloud - works from scratch

set -e

echo "🚀 ThisIsCloud Deployment Script"
echo "==================================="

# Allow running as root or via sudo
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  You are running this script as root. This is allowed but not recommended."
    read -p "Continue as root? (y/N): " CONT
    if [ "${CONT,,}" != "y" ]; then
        echo "Aborting. Re-run as a non-root deployment user or re-run and answer 'y' to continue."
        exit 1
    fi
    SUDO_CMD=""
    DEPLOY_USER=${SUDO_USER:-root}
else
    SUDO_CMD="sudo"
    DEPLOY_USER=$USER
fi

# Configuration
read -p "Enter your domain name (e.g., files.example.com): " DOMAIN
# Validate domain is not empty
while [ -z "$DOMAIN" ]; do
    echo "⚠️  Domain cannot be empty!"
    read -p "Enter your domain name (e.g., files.example.com): " DOMAIN
done

read -s -p "Enter database password: " DB_PASSWORD
echo
# Validate password is not empty
while [ -z "$DB_PASSWORD" ]; do
    echo "⚠️  Password cannot be empty!"
    read -s -p "Enter database password: " DB_PASSWORD
    echo
done

read -p "Install location [/var/www/ThisIsCloud]: " INSTALL_DIR
INSTALL_DIR=${INSTALL_DIR:-/var/www/ThisIsCloud}

# Generate secret key
SECRET_KEY=$(openssl rand -hex 32)

echo ""
echo "📦 Installing system dependencies..."
$SUDO_CMD apt update
$SUDO_CMD apt install -y python3-pip python3-venv nginx postgresql certbot python3-certbot-nginx git

echo ""
echo "🗄️  Setting up PostgreSQL..."

# Check if proxychains is active and warn about localhost exclusion
if [ -n "$LD_PRELOAD" ] && echo "$LD_PRELOAD" | grep -q "proxychains"; then
    echo "⚠️  Proxychains detected. Ensuring localhost (127.0.0.1) is not proxied..."
    # Check proxychains config for localnet exclusion
    PROXY_CONF="/etc/proxychains4.conf"
    if [ ! -f "$PROXY_CONF" ]; then
        PROXY_CONF="/etc/proxychains.conf"
    fi
    if [ -f "$PROXY_CONF" ]; then
        if ! grep -q "^localnet 127.0.0.0/255.0.0.0" "$PROXY_CONF"; then
            echo "⚠️  WARNING: proxychains may intercept localhost connections!"
            echo "   Add this line to $PROXY_CONF under [ProxyList]:"
            echo "   localnet 127.0.0.0/255.0.0.0"
            echo ""
        fi
    fi
fi

# Check PostgreSQL version
PG_VERSION=$(sudo -u postgres psql -tAc "SELECT version();" | grep -oP "PostgreSQL \K[0-9]+")
echo "Detected PostgreSQL version: $PG_VERSION"

# Check if database exists
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='filehosting'")

if [ "$DB_EXISTS" = "1" ]; then
    echo "⚠️  Database 'filehosting' already exists"
    read -p "Rebuild from scratch? This will DELETE ALL DATA! (y/N): " REBUILD
    if [ "${REBUILD,,}" = "y" ]; then
        echo "🗑️  Dropping existing database..."
        sudo -u postgres psql -c "DROP DATABASE filehosting;"
        sudo -u postgres psql -c "CREATE DATABASE filehosting;"
        echo "✅ Database recreated"
    else
        echo "Using existing database"
    fi
else
    sudo -u postgres psql -c "CREATE DATABASE filehosting;"
    echo "✅ Database created"
fi

# Create user if doesn't exist, otherwise update password
USER_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='fileuser'")
if [ "$USER_EXISTS" != "1" ]; then
    sudo -u postgres psql -c "CREATE USER fileuser WITH PASSWORD '$DB_PASSWORD';"
    echo "✅ User created"
else
    echo "User 'fileuser' exists, updating password..."
    sudo -u postgres psql -c "ALTER USER fileuser WITH PASSWORD '$DB_PASSWORD';"
fi

# Grant all necessary permissions (PostgreSQL 15+ compatible)
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE filehosting TO fileuser;"
sudo -u postgres psql -d filehosting -c "GRANT ALL ON SCHEMA public TO fileuser;"
sudo -u postgres psql -d filehosting -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fileuser;"
sudo -u postgres psql -d filehosting -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fileuser;"
sudo -u postgres psql -d filehosting -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO fileuser;"
sudo -u postgres psql -d filehosting -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO fileuser;"

echo "✅ Database permissions configured"

echo ""
echo "📁 Setting up application directory..."
$SUDO_CMD mkdir -p $INSTALL_DIR
$SUDO_CMD chown $DEPLOY_USER:$DEPLOY_USER $INSTALL_DIR

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Updating existing installation..."
    cd $INSTALL_DIR
    # Allow proxychains for git (needed for GitHub access in some environments)
    git pull
else
    echo "Cloning repository..."
    REPO_URL="https://github.com/newnewsposes/http-web-next.git"
    # Allow proxychains for git clone (needed for GitHub access)
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd $INSTALL_DIR
fi

echo ""
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

echo ""
echo "💾 Creating database tables..."
export SECRET_KEY="$SECRET_KEY"
export DATABASE_URL="postgresql://fileuser:$DB_PASSWORD@localhost/filehosting"

# Create all tables using db.create_all()
# IMPORTANT: Unset LD_PRELOAD to bypass proxychains for localhost PostgreSQL
env -u LD_PRELOAD python3 - <<'PY'
from app import create_app, db

app = create_app()
with app.app_context():
    print('Creating database tables...')
    db.create_all()
    print('✅ Database tables created successfully')
PY

echo ""
echo "👤 Creating admin user..."
read -p "Admin username [admin]: " ADMIN_USER
ADMIN_USER=${ADMIN_USER:-admin}
read -p "Admin email: " ADMIN_EMAIL
read -s -p "Admin password: " ADMIN_PASS
echo

# Create admin user without proxychains
env -u LD_PRELOAD python3 << EOF
from app import create_app, db
from app.models.user import User

app = create_app()
with app.app_context():
    # Check if admin exists
    admin = User.query.filter_by(username='$ADMIN_USER').first()
    if not admin:
        admin = User(username='$ADMIN_USER', email='$ADMIN_EMAIL', is_admin=True)
        admin.set_password('$ADMIN_PASS')
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin user created")
    else:
        print("ℹ️  Admin user already exists")
EOF

echo ""
echo "🔧 Creating systemd service..."
$SUDO_CMD tee /etc/systemd/system/ThisIsCloud.service > /dev/null << EOF
[Unit]
Description=ThisIsCloud file hosting platform
After=network.target postgresql.service

[Service]
User=$DEPLOY_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin"
Environment="SECRET_KEY=$SECRET_KEY"
Environment="DATABASE_URL=postgresql://fileuser:$DB_PASSWORD@localhost/filehosting"
Environment="SESSION_COOKIE_SECURE=True"
ExecStart=$INSTALL_DIR/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 --timeout 300 run:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

$SUDO_CMD systemctl daemon-reload
$SUDO_CMD systemctl enable ThisIsCloud
$SUDO_CMD systemctl start ThisIsCloud

echo ""
echo "🌐 Configuring Nginx..."
$SUDO_CMD tee /etc/nginx/sites-available/ThisIsCloud > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;

    client_max_body_size 500M;
    client_body_timeout 300s;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /static {
        alias $INSTALL_DIR/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /HostedFiles {
        internal;
        alias $INSTALL_DIR/HostedFiles;
    }
}
EOF

$SUDO_CMD ln -sf /etc/nginx/sites-available/ThisIsCloud /etc/nginx/sites-enabled/
$SUDO_CMD nginx -t
$SUDO_CMD systemctl restart nginx

echo ""
echo "🔒 Setting up SSL certificate..."
$SUDO_CMD certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $ADMIN_EMAIL || echo "⚠️  SSL setup failed. Run manually: sudo certbot --nginx -d $DOMAIN"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Summary:"
echo "==========="
echo "URL: https://$DOMAIN"
echo "Admin user: $ADMIN_USER"
echo "Install location: $INSTALL_DIR"
echo ""
echo "🔧 Management commands:"
echo "$SUDO_CMD systemctl status ThisIsCloud   # Check status"
echo "$SUDO_CMD systemctl restart ThisIsCloud  # Restart app"
echo "$SUDO_CMD systemctl stop ThisIsCloud     # Stop app"
echo "$SUDO_CMD journalctl -u ThisIsCloud -f   # View logs"
echo ""
echo "🎉 Your file hosting platform is ready!"
