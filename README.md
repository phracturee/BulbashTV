# BulbashTV

**BulbashTV** is a web application for discovering and streaming movies and TV shows via torrent integration. It uses TMDB API for metadata and searches multiple torrent trackers.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
  - [Docker (Recommended)](#docker-recommended)
  - [Local Installation](#local-installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Caching](#caching)
- [Diagnostics](#diagnostics)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Features

- **Movie and TV Show Catalog** — TMDB integration with Russian language support
- **Seasons and Episodes Page** — Easy episode selection with descriptions, ratings, and air dates
- **Torrent Search** — Integration with multiple trackers:
  - **RuTracker** — Direct integration, up to 500 results (requires cookies, up to 10 pages)
  - **Rutor** — No authorization required, up to 125 results (5 pages)
  - **LostFilm** — HD movies and TV shows with dubbing (automatic torrent download)
- **TV Show Playback** — Smart season search with SXXEYY pattern filtering
- **Result Pagination** — Gradual torrent loading (30 results per page with "Load More" button)
- **Favorites** — Content organization by folders
- **Watched History** — Track watched movies and episodes
- **Search History** — Save search queries
- **Torrent Streaming** — Playback via server.js + mpv
- **Image Caching** — Local poster caching
- **Torrent Prioritization** — Remember selected releases
- **Clean Interface** — Modern design with rounded elements and background images

---

## Architecture

The application follows **separation of concerns** principle using OOP:

```
BulbashTVApp (Flask application factory)
├── TMDBClient (TMDB API communication)
├── FavoritesManager (Persistent favorites storage)
├── HistoryManager (Search/watch history)
├── MediaFormatter + ImageCache (Data formatting, image caching)
└── TorrentManager (Search, caching, streaming)
    └── TorrentSearcher (Multi-tracker search)
```

### Key Classes

| Class | File | Description |
|-------|------|-------------|
| `BulbashTVApp` | `app.py` | Flask app factory, route registration |
| `TMDBClient` | `services/tmdb_client.py` | TMDB API client with retry logic |
| `TorrentManager` | `services/torrent_manager.py` | Torrent search, cache, streaming |
| `TorrentSearcher` | `torrent_search.py` | Multi-tracker search implementation |
| `FavoritesManager` | `services/data_manager.py` | Favorites folder management |
| `MediaFormatter` | `services/media_formatter.py` | Format TMDB data for templates |

---

## Installation

### Docker (Recommended)

The easiest way to run the application is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/phracturee/BulbashTV.git
cd BulbashTV

# Setup configuration
cp config.py.example config.py
# Edit config.py and add your TMDB API key

# Build and run
docker-compose up -d

# View logs
docker-compose logs -f
```

The application will be available at: **http://localhost:5000**

**For detailed Docker installation:** see [DOCKER.md](DOCKER.md)

---

### Local Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/phracturee/BulbashTV.git
cd BulbashTV
```

#### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Install Node.js Dependencies

```bash
npm install
```

This installs `webtorrent` and `webtorrent-cli` required for streaming.

#### 4. Install mpv (for playback)

```bash
# Ubuntu/Debian
sudo apt install mpv

# macOS
brew install mpv

# Windows
# Download from https://mpv.io/installation/
```

#### 5. Setup Configuration

```bash
cp config.py.example config.py
```

Edit `config.py` and add your TMDB API key.

---

## Configuration

### Configuration File (config.py)

```python
# TMDB API Configuration
# Get your API key from: https://www.themoviedb.org/settings/api
TMDB_API_KEY = "your_api_key_here"

# Custom DNS (optional)
# Recommended: "8.8.8.8" (Google), "1.1.1.1" (Cloudflare), "9.9.9.9" (Quad9)
CUSTOM_DNS = ""

# TMDB API Base URL
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Torrent download directory (optional)
# Leave empty to use system temp directory
TORRENT_DOWNLOAD_DIR = ""
```

### Setting up Cookies for RuTracker

RuTracker requires authorization. Instead of login/password, cookies are used:

1. Log in to rutracker.org through your browser
2. Export cookies (e.g., using "EditThisCookie" extension)
3. Save to `cookies/rutracker_cookies.json`

**Cookies file format:**
```json
[
  {"name": "bb_data", "value": "...", "domain": ".rutracker.org"},
  {"name": "bb_session", "value": "...", "domain": ".rutracker.org"}
]
```

**Rutor** does not require authorization and works immediately.

---

## Usage

### Start the Application

```bash
python app.py
```

The application will be available at: **http://localhost:5000**

### Search for Torrents

1. Open a movie/TV show page
2. Click the torrent search button
3. Select a torrent from the list
4. Click "Watch" to start streaming

### Manage Favorites

- Create folders to organize content
- Add movies/TV shows to favorites
- Quick access via the "Favorites" menu

### Watch TV Shows

1. Open the TV show page
2. Click "Watch" to go to seasons
3. Select a season from the list on the left
4. Choose an episode to view information
5. Click "Watch" to start playback

---

## API Endpoints

### Content

| Endpoint | Description |
|----------|-------------|
| `GET /api/movies` | Get list of movies |
| `GET /api/tv-shows` | Get list of TV shows |
| `GET /api/trending` | Get trending content |
| `GET /api/search?q=query` | Search content |

### Favorites

| Endpoint | Description |
|----------|-------------|
| `GET /api/favorites/folders` | Get all folders |
| `POST /api/favorites/folders` | Create folder |
| `PUT /api/favorites/folders/<id>` | Rename folder |
| `DELETE /api/favorites/folders/<id>` | Delete folder |
| `POST /api/favorites/add` | Add to favorites |
| `DELETE /api/favorites/remove/<id>` | Remove from favorites |

### Torrents

| Endpoint | Description |
|----------|-------------|
| `GET /api/torrents/search?q=query` | Search all trackers (RuTracker + Rutor) |
| `GET /api/torrents/search/rutracker?q=query` | Search RuTracker |
| `GET /api/torrents/search/rutor?q=query` | Search Rutor |
| `POST /api/torrent/start` | Start streaming |
| `GET /api/torrent/status` | Get status |
| `POST /api/torrent/stop` | Stop streaming |
| `DELETE /api/torrent/cache/clear` | Clear torrent cache |

### Diagnostics

| Endpoint | Description |
|----------|-------------|
| `GET /api/diagnostics` | Check TMDB connection |

---

## Project Structure

```
BulbashTV/
├── app.py                      # Main Flask application
├── config.py                   # Configuration (do not commit)
├── config.py.example           # Configuration template
├── torrent_search.py           # Torrent search
├── server.js                   # Torrent streaming via MPV
├── requirements.txt            # Python dependencies
├── package.json                # Node.js dependencies
├── models/
│   └── __init__.py            # Data models
├── services/
│   ├── __init__.py
│   ├── tmdb_client.py         # TMDB API client
│   ├── data_manager.py        # Data management
│   ├── media_formatter.py     # Media formatting
│   └── torrent_manager.py     # Torrent management
├── parsers/
│   ├── __init__.py            # Base Spider class
│   ├── rutor.py               # Rutor parser
│   └── rutracker.py           # RuTracker parser (multi-page)
├── utils/
│   └── http.py                # HTTP utilities
├── templates/                  # HTML templates
│   ├── index.html             # Home page
│   ├── movie.html             # Movie/TV show page
│   ├── tv_episodes.html       # TV show episodes page
│   ├── category.html          # Category catalog
│   ├── search.html            # Search page
│   ├── favorites.html         # Favorites page
│   └── folder_items.html      # Folder items page
├── static/                     # Static files
│   ├── css/style.css          # Main styles
│   └── img/                   # Cached images (not committed)
│       └── .gitkeep           # Empty file to preserve structure
├── data/                       # Application data (not committed)
│   ├── favorites.json         # User favorites
│   ├── search_history.json    # Search history
│   ├── selected_torrents.json # Selected torrents
│   ├── torrent_cache.json     # Torrent search cache
│   └── playback_progress.json # Playback progress
├── logs/                       # Logs (not committed)
│   └── app.log                # Application log
├── downloads/                  # Downloads (not committed)
└── cookies/                    # Tracker cookies (not committed)
    └── .gitkeep               # Empty file to preserve structure
```

---

## Requirements

### Mandatory

- **Python 3.9+**
- **Node.js 16+** (for webtorrent-cli)
- **TMDB API key** (get from https://www.themoviedb.org/settings/api)
- **mpv** (for video playback)

### Optional

- **Tor** — for anonymous search
- **Git** — for cloning the repository

### Python Dependencies

```
flask>=3.0.0
requests[socks]>=2.31.0
PySocks>=1.7.1
beautifulsoup4>=4.12.0
lxml>=4.9.0
```

### Node.js Dependencies

```
webtorrent
webtorrent-cli
```

---

## Caching

### How It Works

Torrent search results are cached for **1 hour**.

**Files:**
- `data/torrent_cache.json` — search results cache
- `data/selected_torrents.json` — user-selected releases
- `data/torrent_history.json` — watch history
- `data/playback_progress.json` — playback progress

**Logic:**
```
1. User searches for "movie"
   ↓
2. Check cache:
   - Valid cache exists (< 1 hour)? → Return from cache
   - Cache expired or missing? → Search again
   ↓
3. Save results to cache
   ↓
4. Return results to user
```

### Cache Configuration

In `services/torrent_manager.py`:
```python
CACHE_DURATION = 3600  # 1 hour (in seconds)
```

Change to desired value:
- `1800` = 30 minutes
- `7200` = 2 hours
- `86400` = 24 hours

### Clear Cache

**Via API:**
```bash
curl -X DELETE http://localhost:5000/api/torrent/cache/clear
```

**Manually:**
```bash
rm data/torrent_cache.json
```

### Benefits

1. **Fast search** — results returned instantly from cache
2. **Less load** — no need to query trackers every time
3. **Traffic savings** — fewer requests to external APIs

---

## Diagnostics

### Check TMDB Connection

```bash
curl http://localhost:5000/api/diagnostics
```

**Successful response:**
```json
{
  "overall_status": "ok",
  "tests": {
    "dns": {"status": "ok", "ip": "xxx.xxx.xxx.xxx"},
    "tmdb": {"status": "ok", "response_time": 0.5}
  }
}
```

### Check Tracker Availability

```bash
curl "http://localhost:5000/api/torrents/search?q=test"
```

### Check Logs

```bash
# Application logs
tail -f logs/app.log

# Streaming logs
tail -f /tmp/striming-torrent-mpv.log
```

---

## Troubleshooting

### TMDB Connection Error

**Problem:** `Connection refused`

**Solutions:**
1. Check DNS: `nslookup api.themoviedb.org`
2. Use VPN or Tor
3. Change DNS to `8.8.8.8` or `1.1.1.1`
4. Check API key in `config.py`

### Russian Trackers Not Working

**Problem:** Search doesn't find content

**Solution:**
1. RuTracker and Rutor are integrated directly
2. RuTracker requires cookies (see [Setting up Cookies](#setting-up-cookies-for-rutracker))
3. Check logs: `cat logs/app.log`

### Streaming Errors

**Problem:** Video doesn't play

**Solutions:**
1. Make sure `mpv` is installed: `sudo apt install mpv`
2. Check streaming logs: `cat /tmp/striming-torrent-mpv.log`
3. Check application logs: `cat logs/app.log`
4. Update dependencies: `npm update`

### Performance Issues

**Problem:** Slow torrent loading

**Solutions:**
1. Reduce `max_pages` for RuTracker in `torrent_search.py`
2. Use search caching (enabled by default)
3. Configure proxy or VPN for faster access

### "No module named ..." Error

**Problem:** Python dependencies not installed

**Solution:**
```bash
pip install -r requirements.txt
```

### "Cannot find module ..." Error

**Problem:** Node.js dependencies not installed

**Solution:**
```bash
npm install
```

### JSON Serialization Error

**Problem:** `Object of type TorrentResult is not JSON serializable`

**Solution:** Update `app.py` and `services/torrent_manager.py` to latest version (convert to dictionaries)

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

---

## Contact

- **Issues:** GitHub Issues
- **Repository:** https://github.com/phracturee/BulbashTV

---

## License

This project is created for educational purposes.

---

**BulbashTV** © 2024-2025
