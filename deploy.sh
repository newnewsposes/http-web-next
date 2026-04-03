#!/bin/bash
# Deployment script for HaloDrop

set -e

echo "🚀 HaloDrop Deployment Script"
echo "==================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "❌ Please don't run as root. Run as your deployment user."
    exit 1
fi

# Configuration
read -p "Enter your domain name (e.g., files.example.com): " DOMAIN
read -s -p "Enter database password: " DB_PASSWORD
echo
read -p "Install location [/var/www/HaloDrop]: " INSTALL_DIR
INSTALL_DIR=${INSTALL_DIR:-/var/www/HaloDrop}

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
    git clone https://github.com/newnewsposes/HaloDrop.git $INSTALL_DIR
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
sudo tee /etc/systemd/system/HaloDrop.service > /dev/null << EOF
[Unit]
Description=HaloDrop file hosting platform
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
sudo systemctl enable HaloDrop
sudo systemctl start HaloDrop

echo ""
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/HaloDrop > /dev/null << EOF
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

sudo ln -sf /etc/nginx/sites-available/HaloDrop /etc/nginx/sites-enabled/
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
echo "sudo systemctl status HaloDrop   # Check status"
echo "sudo systemctl restart HaloDrop  # Restart app"
echo "sudo systemctl stop HaloDrop     # Stop app"
echo "sudo journalctl -u HaloDrop -f   # View logs"
echo ""
echo "🎉 Your file hosting platform is ready!"
