# http-web-next

A modern, production-ready file hosting platform built with Flask.

## Features

✨ **Current (Phase 1 - Backend Structure)**
- Clean modular architecture (blueprints, models, services)
- SQLite database with SQLAlchemy ORM
- File upload with metadata tracking
- Unique share links for each file
- Download counting
- Modern dark-themed UI

🚀 **Coming Soon**
- User authentication & authorization
- Chunked file uploads for large files
- Analytics dashboard
- Rate limiting
- Advanced file previews (images, videos, PDFs)
- Dark/light theme toggle

## Quick Start

```bash
# Clone the repository
git clone https://github.com/newnewsposes/http-web-next.git
cd http-web-next

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Run the application
python run.py
```

Visit http://localhost:5000/files/ in your browser.

## Project Structure

```
http-web-next/
├── app/
│   ├── __init__.py           # App factory
│   ├── blueprints/           # Route blueprints
│   │   └── files.py
│   ├── models/               # Database models
│   │   └── file.py
│   ├── services/             # Business logic (future)
│   ├── templates/            # Jinja2 templates
│   │   ├── auth/
│   │   └── files/
│   │       └── index.html
│   └── static/               # CSS, JS, assets
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── main.js
├── migrations/               # Database migrations
├── HostedFiles/             # Uploaded files storage
├── run.py                   # Application entry point
└── requirements.txt         # Python dependencies
```

## Configuration

Set environment variables for production:

```bash
export SECRET_KEY="your-secret-key-here"
export DATABASE_URL="sqlite:///production.db"  # or PostgreSQL URL
```

## License

MIT

---

**Phase 1 Complete** - Backend structure, file upload/download, and basic UI are ready!
