# PhotoShare

PhotoShare is a Flask web application for creating photo albums, uploading photos, tagging images, commenting, liking photos, adding friends, and discovering content through search, leaderboards, and recommendations.

The app includes a polished responsive interface with shared templates, reusable photo-card layouts, account pages, album management, friend recommendations, tag-based photo search, comment search, and a contributor leaderboard.

Live GitHub Pages preview: https://kevkim12.github.io/portfolio/photoshare-live/

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

The screenshots below are generated from the local SQLite demo database. For a broader tour, open the live GitHub Pages preview linked above.

<table>
  <tr>
    <td align="center"><strong>Redesigned Home</strong></td>
    <td align="center"><strong>Album Photos</strong></td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/01-home-public.png" alt="PhotoShare public home page" width="420"></td>
    <td><img src="docs/screenshots/05-album-photos.png" alt="PhotoShare album photo grid" width="420"></td>
  </tr>
  <tr>
    <td align="center"><strong>Tag Search</strong></td>
    <td align="center"><strong>Upload Flow</strong></td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/10-photo-search-results.png" alt="PhotoShare tag search results" width="420"></td>
    <td><img src="docs/screenshots/13-upload.png" alt="PhotoShare upload form" width="420"></td>
  </tr>
</table>

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
