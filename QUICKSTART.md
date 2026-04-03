# 🚀 Quick Start Guide

## Local Development (Test Everything)

```bash
cd /root/.openclaw/workspace/HaloDrop

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
flask db upgrade

# Create admin user
python3 << 'EOF'
from app import create_app, db
from app.models.user import User

app = create_app()
with app.app_context():
    admin = User(username='admin', email='admin@test.com', is_admin=True)
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print("✅ Admin created: admin / admin123")
EOF

# Run development server
python run.py
```

Visit: http://localhost:5000

**Test checklist:**
1. Register new account
2. Upload small file (drag & drop)
3. Upload large file (watch progress)
4. Login as admin (admin/admin123)
5. View admin dashboard
6. Manage users
7. View analytics

---

## Production Deployment (Ubuntu VPS)

### Option 1: One-Click Script

```bash
# On your VPS
git clone https://github.com/newnewsposes/HaloDrop.git
cd HaloDrop
chmod +x deploy.sh
./deploy.sh
```

Follow prompts. Script handles:
- PostgreSQL setup
- Nginx configuration
- SSL certificate
- Systemd service
- Admin user creation

### Option 2: Docker

```bash
# Clone repo
git clone https://github.com/newnewsposes/HaloDrop.git
cd HaloDrop

# Set environment
export SECRET_KEY=$(openssl rand -hex 32)

# Start services
docker-compose up -d

# Create admin
docker-compose exec web flask shell
>>> from app import db
>>> from app.models.user import User
>>> admin = User(username='admin', email='admin@example.com', is_admin=True)
>>> admin.set_password('secure-password')
>>> db.session.add(admin)
>>> db.session.commit()
>>> exit()
```

---

## Management Commands

```bash
# View logs
sudo journalctl -u HaloDrop -f

# Restart service
sudo systemctl restart HaloDrop

# Database migrations
source venv/bin/activate
flask db migrate -m "Description"
flask db upgrade

# Create admin user
flask shell
>>> from app import db
>>> from app.models.user import User
>>> admin = User(username='newadmin', email='admin@example.com', is_admin=True)
>>> admin.set_password('password')
>>> db.session.add(admin)
>>> db.session.commit()

# Change user quota
>>> user = User.query.filter_by(username='johndoe').first()
>>> user.storage_quota = 10 * 1024 * 1024 * 1024  # 10GB
>>> db.session.commit()
```

---

## Customization

### Change branding
Edit `app/templates/base.html`:
```html
<a href="{{ url_for('files.index') }}" class="logo">📁 YOUR-NAME</a>
```

### Adjust file size limit
Edit `app/__init__.py`:
```python
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024  # 1GB
```

### Change default quota
Edit `app/models/user.py`:
```python
storage_quota = db.Column(db.BigInteger, default=10*1024*1024*1024)  # 10GB
```

### Adjust rate limits
Edit `app/blueprints/api.py`:
```python
@rate_limit(max_requests=200, window_seconds=60)  # 200 per minute
```

---

## Troubleshooting

### Database errors
```bash
cd /root/.openclaw/workspace/HaloDrop
source venv/bin/activate
flask db stamp head
flask db migrate
flask db upgrade
```

### Permission errors
```bash
sudo chown -R www-data:www-data HostedFiles/
sudo chmod -R 755 HostedFiles/
```

### Service won't start
```bash
sudo journalctl -u HaloDrop -n 50
```

### Can't login
```bash
# Reset admin password
flask shell
>>> from app import db
>>> from app.models.user import User
>>> admin = User.query.filter_by(username='admin').first()
>>> admin.set_password('newpassword')
>>> db.session.commit()
```

---

## Next Steps

1. **Test locally** - Run development server and try all features
2. **Deploy to VPS** - Use deploy.sh for production
3. **Configure domain** - Point DNS to your VPS
4. **Set up backups** - Automate database dumps
5. **Monitor logs** - Set up log rotation
6. **Customize branding** - Make it yours!

---

Repository: https://github.com/newnewsposes/HaloDrop
Full docs: See README.md and PROJECT-COMPLETE.md
