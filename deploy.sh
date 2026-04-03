#!/bin/bash
# Deployment script for ThisIsCloud

set -e

echo "🚀 ThisIsCloud Deployment Script"
echo "==================================="

# Allow running as root or via sudo. If running as root, warn and confirm.
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  You are running this script as root. This is allowed but not recommended."
    read -p "Continue as root? (y/N): " CONT
    if [ "${CONT,,}" != "y" ]; then
        echo "Aborting. Re-run as a non-root deployment user or re-run and answer 'y' to continue."
        exit 1
    fi
    SUDO=""
    # If script was invoked via sudo, SUDO_USER may be set to the invoking user
    DEPLOY_USER=${SUDO_USER:-root}
else
    SUDO="sudo"
    DEPLOY_USER=$USER
fi

# Configuration
read -p "Enter your domain name (e.g., files.example.com): " DOMAIN
read -s -p "Enter database password: " DB_PASSWORD
echo
read -p "Install location [/var/www/ThisIsCloud]: " INSTALL_DIR
INSTALL_DIR=${INSTALL_DIR:-/var/www/ThisIsCloud}

# Generate secret key
SECRET_KEY=$(openssl rand -hex 32)

echo ""
echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y python3-pip python3-venv nginx postgresql certbot python3-certbot-nginx

echo ""
echo "🗄️  Setting up PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE filehosting;" || true
sudo -u postgres psql -c "CREATE USER fileuser WITH PASSWORD '$DB_PASSWORD';" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE filehosting TO fileuser;"

echo ""
echo "📁 Setting up application directory..."
sudo mkdir -p $INSTALL_DIR
sudo chown $USER:$USER $INSTALL_DIR

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "Updating existing installation..."
    cd $INSTALL_DIR
    git pull
else
    echo "Cloning repository..."
    # Prefer public http-web-next repo and attempt clone without using http(s) proxy
    REPO_URL="https://github.com/newnewsposes/http-web-next.git"
    # Try non-proxied clone first to avoid proxychains prompting for credentials
    if env -u http_proxy -u https_proxy GIT_TERMINAL_PROMPT=0 git clone "$REPO_URL" "$INSTALL_DIR"; then
        echo "Cloned via direct connection"
    else
        echo "Direct clone failed — falling back to normal git clone (may prompt for credentials)"
        git clone "$REPO_URL" "$INSTALL_DIR"
    fi
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
echo "💾 Running database migrations..."
export SECRET_KEY="$SECRET_KEY"
export DATABASE_URL="postgresql://fileuser:$DB_PASSWORD@localhost/filehosting"

# Initialize migrations directory if missing, then run migrate & upgrade
if [ ! -d "migrations" ]; then
    echo "migrations folder not found — initializing Alembic (flask db init)"
    flask db init || true
    echo "Creating initial migration (if models present)"
    flask db migrate -m "Initial migration" || true
fi

# Apply migrations (upgrade)
flask db upgrade

echo ""
echo "👤 Creating admin user..."
read -p "Admin username [admin]: " ADMIN_USER
ADMIN_USER=${ADMIN_USER:-admin}
read -p "Admin email: " ADMIN_EMAIL
read -s -p "Admin password: " ADMIN_PASS
echo

python3 << EOF
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
sudo tee /etc/systemd/system/ThisIsCloud.service > /dev/null << EOF
[Unit]
Description=ThisIsCloud file hosting platform
After=network.target postgresql.service

[Service]
User=$USER
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

sudo systemctl daemon-reload
sudo systemctl enable ThisIsCloud
sudo systemctl start ThisIsCloud

echo ""
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/ThisIsCloud > /dev/null << EOF
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

sudo ln -sf /etc/nginx/sites-available/ThisIsCloud /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo ""
echo "🔒 Setting up SSL certificate..."
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $ADMIN_EMAIL || echo "⚠️  SSL setup failed. Run manually: sudo certbot --nginx -d $DOMAIN"

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
echo "sudo systemctl status ThisIsCloud   # Check status"
echo "sudo systemctl restart ThisIsCloud  # Restart app"
echo "sudo systemctl stop ThisIsCloud     # Stop app"
echo "sudo journalctl -u ThisIsCloud -f   # View logs"
echo ""
echo "🎉 Your file hosting platform is ready!"
