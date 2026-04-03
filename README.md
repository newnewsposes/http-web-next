# http-web-next 🚀

> **A modern, production-ready file hosting platform with advanced features**

Built with Flask • SQLAlchemy • Modern JavaScript • Dark UI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## ✨ Features

### 🔐 User Management
- **User authentication** with registration, login, and session management
- **Password hashing** using Werkzeug's secure methods
- **Storage quotas** (default 5GB per user, configurable)
- **Admin system** with role-based access control
- **User profiles** with storage statistics

### 📁 File Management
- **Chunked uploads** for large files (resumable, progress tracking)
- **Drag & drop interface** with visual feedback
- **Public/private files** with permission system
- **Share links** with unique tokens
- **File type icons** and metadata display
- **Download tracking** and analytics

### 📊 Admin Dashboard
- **System statistics** (users, files, storage, downloads)
- **User management** (activate/deactivate, quotas, admin privileges)
- **File management** with bulk operations
- **Analytics charts** (upload trends, file types, storage distribution)
- **Top uploaders** and most downloaded files

### 🛡️ Security
- **Rate limiting** on API endpoints
- **CSRF protection** for forms
- **Security headers** (CSP, X-Frame-Options, etc.)
- **Secure sessions** with HttpOnly cookies
- **Input validation** and sanitization
- **Permission checks** on all file operations

### 🎨 Modern UI
- **Dark theme** with smooth gradients
- **Responsive design** (mobile-friendly)
- **Real-time progress bars** for uploads
- **Toast notifications** for user feedback
- **Card-based file grid** with hover effects

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip
- (Optional) PostgreSQL for production

### Installation

```bash
# Clone the repository
git clone https://github.com/newnewsposes/http-web-next.git
cd http-web-next

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Run development server
python run.py
```

Visit **http://localhost:5000**

---

## 📁 Project Structure

```
http-web-next/
├── app/
│   ├── __init__.py              # App factory
│   ├── blueprints/              # Route handlers
│   │   ├── admin.py             # Admin dashboard
│   │   ├── api.py               # Chunked upload API
│   │   ├── auth.py              # Authentication
│   │   └── files.py             # File operations
│   ├── models/                  # Database models
│   │   ├── file.py              # File metadata
│   │   └── user.py              # User accounts
│   ├── services/                # Business logic
│   │   ├── preview.py           # File previews
│   │   └── upload.py            # Chunked uploads
│   ├── utils/                   # Utilities
│   │   └── security.py          # Rate limiting, validation
│   ├── static/                  # CSS, JS, assets
│   │   ├── css/style.css
│   │   └── js/upload.js
│   └── templates/               # Jinja2 templates
│       ├── base.html
│       ├── admin/
│       ├── auth/
│       └── files/
├── migrations/                  # Database migrations
├── HostedFiles/                 # Uploaded files storage
│   ├── chunks/                  # Temporary upload chunks
│   └── previews/                # Generated thumbnails
├── run.py                       # Application entry point
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Required for production
export SECRET_KEY="your-super-secret-key-here"
export DATABASE_URL="postgresql://user:pass@localhost/dbname"
export SESSION_COOKIE_SECURE="True"  # HTTPS only

# Optional
export MAX_CONTENT_LENGTH=524288000  # 500MB default
```

### config.py (optional)

Create `config.py` in the root directory:

```python
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///files.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'HostedFiles'
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB

class ProductionConfig(Config):
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
```

---

## 🚢 Deployment

### Option 1: Traditional Server (Ubuntu + Nginx + Gunicorn)

#### 1. Install system dependencies

```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx postgresql
```

#### 2. Set up PostgreSQL

```bash
sudo -u postgres psql
CREATE DATABASE filehosting;
CREATE USER fileuser WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE filehosting TO fileuser;
\q
```

#### 3. Configure application

```bash
cd /var/www/http-web-next
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

export SECRET_KEY="$(openssl rand -hex 32)"
export DATABASE_URL="postgresql://fileuser:yourpassword@localhost/filehosting"
export SESSION_COOKIE_SECURE="True"

flask db upgrade
```

#### 4. Create systemd service

`/etc/systemd/system/http-web-next.service`:

```ini
[Unit]
Description=http-web-next file hosting
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/http-web-next
Environment="PATH=/var/www/http-web-next/venv/bin"
Environment="SECRET_KEY=your-secret-key"
Environment="DATABASE_URL=postgresql://fileuser:yourpassword@localhost/filehosting"
Environment="SESSION_COOKIE_SECURE=True"
ExecStart=/var/www/http-web-next/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 run:app

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable http-web-next
sudo systemctl start http-web-next
```

#### 5. Configure Nginx

`/etc/nginx/sites-available/http-web-next`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 500M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static {
        alias /var/www/http-web-next/app/static;
        expires 30d;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/http-web-next /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

### Option 2: Docker

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .

RUN flask db upgrade

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "run:app"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=postgresql://fileuser:password@db/filehosting
      - SESSION_COOKIE_SECURE=True
    volumes:
      - ./HostedFiles:/app/HostedFiles
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=filehosting
      - POSTGRES_USER=fileuser
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./HostedFiles:/usr/share/nginx/html/files
    depends_on:
      - web

volumes:
  postgres_data:
```

```bash
docker-compose up -d
```

---

## 👨‍💼 Admin Setup

### Create first admin user

```bash
flask shell
```

```python
from app import db
from app.models.user import User

admin = User(username='admin', email='admin@example.com', is_admin=True)
admin.set_password('secure-password')
db.session.add(admin)
db.session.commit()
exit()
```

---

## 📊 API Reference

### Chunked Upload API

#### POST /api/upload/init
Initialize upload session

**Request:**
```json
{
  "filename": "video.mp4",
  "fileSize": 524288000,
  "mimeType": "video/mp4"
}
```

**Response:**
```json
{
  "uploadId": "uuid",
  "chunkSize": 1048576
}
```

#### POST /api/upload/chunk
Upload chunk

**Form Data:**
- `uploadId`: string
- `chunkIndex`: int
- `chunk`: binary

#### POST /api/upload/complete
Finalize upload

**Request:**
```json
{
  "uploadId": "uuid",
  "totalChunks": 20,
  "filename": "video.mp4",
  "mimeType": "video/mp4",
  "isPublic": true
}
```

---

## 🧪 Testing

```bash
# Run tests (if added)
pytest

# Test chunked upload locally
python -m http.server 5000

# Load test with Apache Bench
ab -n 100 -c 10 http://localhost:5000/
```

---

## 🔧 Troubleshooting

### Database migration issues
```bash
flask db stamp head
flask db migrate
flask db upgrade
```

### Permission errors on uploaded files
```bash
sudo chown -R www-data:www-data HostedFiles/
sudo chmod -R 755 HostedFiles/
```

### Rate limit false positives
Edit `app/utils/security.py` and adjust limits:
```python
@rate_limit(max_requests=100, window_seconds=60)
```

---

## 📈 Roadmap

- [ ] Image/video previews
- [ ] Batch file operations
- [ ] File expiration dates
- [ ] API tokens for programmatic access
- [ ] Two-factor authentication
- [ ] S3-compatible storage backend
- [ ] File scanning (antivirus integration)
- [ ] CDN support
- [ ] Multi-language support

---

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a PR.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

- Flask framework
- Chart.js for analytics
- Font Awesome for icons (optional)
- Community contributors

---

**Built with ❤️ for modern file hosting needs**
