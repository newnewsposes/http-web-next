# Windows Development Setup

## Quick Start (Windows)

### 1. Install Prerequisites

Download and install:
- **Python 3.9+**: https://www.python.org/downloads/
  - ✅ Check "Add Python to PATH" during installation
- **Git**: https://git-scm.com/download/win (if not already installed)

### 2. Clone Repository

```powershell
cd "E:\Git Projects"
git clone https://github.com/newnewsposes/http-web-next.git
cd http-web-next
```

### 3. Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**If you get an error about execution policy:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Initialize Database

```powershell
# Create migrations folder
flask db init

# Create initial migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

### 6. Create Admin User

```powershell
python
```

Then in Python:
```python
from app import create_app, db
from app.models.user import User

app = create_app()
with app.app_context():
    admin = User(username='admin', email='admin@test.com', is_admin=True)
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print("✅ Admin user created: admin / admin123")
    exit()
```

### 7. Run Development Server

```powershell
python run.py
```

Visit: **http://localhost:5000**

Login with: `admin` / `admin123`

---

## Troubleshooting

### "flask: command not found"

```powershell
# Make sure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Or use python -m flask instead
python -m flask db upgrade
```

### "No module named 'app'"

Make sure you're in the project root directory:
```powershell
cd "E:\Git Projects\http-web-next"
```

### Port 5000 already in use

Edit `run.py` and change the port:
```python
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)  # Changed to 5001
```

### Database locked error

Close any other terminals/processes using the database, then:
```powershell
del files.db
flask db upgrade
```
(You'll need to recreate the admin user)

---

## Testing Checklist

1. ✅ Visit http://localhost:5000
2. ✅ Register new user
3. ✅ Login with new user
4. ✅ Upload a small file (drag & drop)
5. ✅ Upload a large file (watch progress bar)
6. ✅ View "My Files"
7. ✅ Download a file
8. ✅ Copy share link
9. ✅ Logout
10. ✅ Login as admin (`admin` / `admin123`)
11. ✅ View Admin Dashboard
12. ✅ Click "Manage Users"
13. ✅ Click "View Analytics"
14. ✅ Try uploading file over quota (should reject)

---

## Production Deployment (Windows Server - IIS)

### Option 1: Deploy to Linux VPS (Recommended)

Windows is for development. For production, deploy to a Linux VPS:

1. **Get a VPS** (DigitalOcean, Linode, Vultr, AWS, etc.)
2. **SSH into server:**
   ```bash
   ssh root@your-server-ip
   ```
3. **Run deployment script:**
   ```bash
   git clone https://github.com/newnewsposes/http-web-next.git
   cd http-web-next
   chmod +x deploy.sh
   ./deploy.sh
   ```

### Option 2: Deploy with Docker (Windows + Docker Desktop)

1. Install **Docker Desktop**: https://www.docker.com/products/docker-desktop/

2. Create `docker-compose.yml` in project root (already exists)

3. Set environment variable:
   ```powershell
   $env:SECRET_KEY = (python -c "import secrets; print(secrets.token_hex(32))")
   ```

4. Start services:
   ```powershell
   docker-compose up -d
   ```

5. Create admin:
   ```powershell
   docker-compose exec web python
   ```
   Then:
   ```python
   from app import create_app, db
   from app.models.user import User
   app = create_app()
   with app.app_context():
       admin = User(username='admin', email='admin@example.com', is_admin=True)
       admin.set_password('secure-password')
       db.session.add(admin)
       db.session.commit()
   exit()
   ```

---

## VS Code Setup (Optional)

1. Open project in VS Code:
   ```powershell
   code .
   ```

2. Install extensions:
   - Python
   - Pylance
   - Jinja

3. Create `.vscode/launch.json`:
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Flask",
         "type": "python",
         "request": "launch",
         "module": "flask",
         "env": {
           "FLASK_APP": "run.py",
           "FLASK_DEBUG": "1"
         },
         "args": ["run", "--no-debugger", "--no-reload"],
         "jinja": true
       }
     ]
   }
   ```

4. Press F5 to debug

---

## Environment Variables (Optional)

Create `.env` file in project root:
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///files.db
SESSION_COOKIE_SECURE=False
```

Install python-dotenv:
```powershell
pip install python-dotenv
```

Edit `app/__init__.py` to load `.env`:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## Common PowerShell Commands

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Deactivate
deactivate

# Run server
python run.py

# Database migrations
flask db init
flask db migrate -m "Message"
flask db upgrade

# Open Python shell
python

# Install package
pip install package-name

# List installed packages
pip list

# Check Python version
python --version

# Check Flask version
flask --version
```

---

## Next Steps

1. **Test locally** - Make sure everything works
2. **Customize** - Change branding, colors, etc.
3. **Deploy** - Use a Linux VPS or Docker for production

---

**For Windows development:** Use the steps above
**For production deployment:** Use Linux (deploy.sh) or Docker
