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

The screenshots below are generated from the local SQLite demo database.

### Public Pages

| Redesigned public home | Log in |
| --- | --- |
| ![PhotoShare public home page](docs/screenshots/01-home-public.png) | ![PhotoShare login page](docs/screenshots/02-login.png) |

| Create account | Browse albums |
| --- | --- |
| ![PhotoShare registration page](docs/screenshots/03-register.png) | ![PhotoShare public albums page](docs/screenshots/04-albums.png) |

| Album photos | Public photo detail |
| --- | --- |
| ![PhotoShare album photo grid](docs/screenshots/05-album-photos.png) | ![PhotoShare public photo detail page](docs/screenshots/06-public-photo-detail.png) |

| Photo search | Comment search |
| --- | --- |
| ![PhotoShare tag search form](docs/screenshots/07-photo-search.png) | ![PhotoShare comment search form](docs/screenshots/08-comment-search.png) |

| Leaderboard | Tag search results |
| --- | --- |
| ![PhotoShare leaderboard page](docs/screenshots/09-leaderboard.png) | ![PhotoShare tag search results](docs/screenshots/10-photo-search-results.png) |

| Comment search results |
| --- |
| ![PhotoShare comment search results](docs/screenshots/11-comment-search-results.png) |

### Signed-in Pages

| Profile dashboard | Upload photo |
| --- | --- |
| ![Signed-in PhotoShare profile dashboard](docs/screenshots/12-profile-kevin.png) | ![PhotoShare upload form](docs/screenshots/13-upload.png) |

| Your albums | Manage photos |
| --- | --- |
| ![PhotoShare user albums page](docs/screenshots/14-your-albums.png) | ![PhotoShare manage photos page](docs/screenshots/15-manage-photos.png) |

| Manage albums | Friends |
| --- | --- |
| ![PhotoShare manage albums page](docs/screenshots/16-manage-albums.png) | ![PhotoShare friends page](docs/screenshots/17-friends.png) |

| Friend recommendations | Photo recommendations |
| --- | --- |
| ![PhotoShare friend recommendations page](docs/screenshots/18-friend-recommendations.png) | ![PhotoShare photo recommendations page](docs/screenshots/19-photo-recommendations.png) |

| Tag page | Logged-in photo detail |
| --- | --- |
| ![PhotoShare tag page](docs/screenshots/20-tag-page.png) | ![Logged-in PhotoShare photo detail page with delete action](docs/screenshots/21-logged-in-photo-detail.png) |

| Likes | Your tag photos |
| --- | --- |
| ![PhotoShare likes page](docs/screenshots/22-likes.png) | ![PhotoShare current user tag photos page](docs/screenshots/23-your-tag-photos.png) |

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
