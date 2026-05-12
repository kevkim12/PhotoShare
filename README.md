# PhotoShare

PhotoShare is a Flask web application for creating photo albums, uploading photos, tagging images, commenting, liking photos, adding friends, and discovering content through search, leaderboards, and recommendations.

The app includes a polished responsive interface with shared templates, reusable photo-card layouts, account pages, album management, friend recommendations, tag-based photo search, comment search, and a contributor leaderboard.

## Technologies Used

- Python
- Flask
- Flask-Login
- Flask-MySQL / PyMySQL
- SQLite for local demo mode
- Jinja templates
- HTML
- CSS
- JavaScript
- SQL

## Features

- User registration and login
- Photo albums and album management
- Photo uploads with captions and tags
- Public album browsing
- Photo likes and comment threads
- Tag search and comment search
- Friend lists and friend recommendations
- Photo recommendations based on tag overlap
- Contributor and popular-tag leaderboards

## Screenshots

| Public home | Photo detail |
| --- | --- |
| ![PhotoShare public home page](docs/screenshots/01-home-public.png) | ![Logged-in photo detail page with tags and comments](docs/screenshots/21-logged-in-photo-detail.png) |

| Tag search | Profile dashboard |
| --- | --- |
| ![Tag search results for travel photos](docs/screenshots/10-photo-search-results.png) | ![Signed-in profile dashboard](docs/screenshots/12-profile-kevin.png) |

## Setup

### 1. Clone The Repository

```bash
git clone <repository-url>
cd photo-sharing-website
```

### 2. Create A Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run With The Local SQLite Demo Database

SQLite mode is the easiest way to run the project locally without installing MySQL.

On Windows PowerShell:

```powershell
$env:PHOTOSHARE_DATABASE="sqlite"
python app.py
```

On macOS or Linux:

```bash
PHOTOSHARE_DATABASE=sqlite python app.py
```

Then open:

```text
http://127.0.0.1:5000/
```

The SQLite database is created automatically at `instance/photoshare.sqlite3`.

### 5. Optional MySQL Setup

To run against MySQL, create the database with the provided schema:

```bash
mysql -u root -p < schema.sql
```

Configure credentials with environment variables:

```powershell
$env:MYSQL_DATABASE_USER="root"
$env:MYSQL_DATABASE_PASSWORD="your-password"
$env:MYSQL_DATABASE_DB="photoshare"
$env:MYSQL_DATABASE_HOST="localhost"
python app.py
```

If no `PHOTOSHARE_DATABASE` value is provided, the app defaults to MySQL.

## Development Notes

- The app runs on port `5000` by default.
- Set `PORT` to use a different port.
- Set `FLASK_DEBUG=true` to run Flask in debug mode.
- Keep generated local files such as `.venv`, `.codex_deps`, `instance`, and server logs out of version control.
