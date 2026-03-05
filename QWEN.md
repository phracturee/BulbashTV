# BulbashTV - Context for Qwen Code

## Project Overview

**BulbashTV** is a Flask-based web application for discovering and streaming movies/TV shows via torrent integration. It uses TMDB API for metadata and searches 15+ torrent trackers (YTS, TPB, RuTracker, Rutor, etc.).

### Key Features
- Movie/TV show catalog with TMDB integration (Russian language support)
- Multi-tracker torrent search with caching (1 hour)
- Favorites management with folders
- Watch history tracking
- Torrent streaming via `webtorrent-cli` + `mpv`
- Image caching for posters/backdrops
- Selected torrent prioritization (remembers last chosen release)

### Tech Stack
- **Backend**: Python 3.9+, Flask 3.0+
- **Frontend**: HTML templates, vanilla JavaScript
- **Torrent**: webtorrent-cli 5.1.3, mpv
- **Data**: JSON files (favorites, history, cache)

## Architecture (OOP Design)

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

| Class | File | Purpose |
|-------|------|---------|
| `BulbashTVApp` | `app.py` | Flask app factory, route registration |
| `TMDBClient` | `services/tmdb_client.py` | TMDB API client with retry logic |
| `TorrentManager` | `services/torrent_manager.py` | Torrent search, cache, streaming |
| `TorrentSearcher` | `torrent_search.py` | Multi-tracker search implementation |
| `FavoritesManager` | `services/data_manager.py` | Favorites folder management |
| `MediaFormatter` | `services/media_formatter.py` | Format TMDB data for templates |

## Building and Running

### Prerequisites
- Python 3.9+
- Node.js 16+
- TMDB API key (get from https://www.themoviedb.org/settings/api)
- mpv (`sudo apt install mpv`)

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install

# Configure (edit config.py with your TMDB API key)
cp config.py.example config.py
```

### Running

```bash
# Start Flask app (default port 5000)
python app.py

# Access at http://localhost:5000
```

### Development

```bash
# Run with debug mode
python app.py  # Debug is enabled by default

# Clear torrent cache
curl -X DELETE http://localhost:5000/api/torrent/cache/clear

# Check diagnostics
curl http://localhost:5000/api/diagnostics
```

## Project Structure

```
BulbashTV/
├── app.py                      # Main Flask app (OOP factory pattern)
├── config.py                   # Configuration (TMDB, trackers, proxies)
├── torrent_search.py           # TorrentSearcher class (978 lines)
├── requirements.txt            # Python dependencies
├── package.json                # Node.js dependencies
├── models/
│   └── __init__.py            # Data models (MediaItem, Movie, TVShow)
├── services/
│   ├── tmdb_client.py         # TMDB API client
│   ├── data_manager.py        # Favorites/History managers
│   ├── media_formatter.py     # Media formatting + ImageCache
│   └── torrent_manager.py     # Torrent search/cache/streaming
├── parsers/
│   ├── __init__.py            # BaseSpider abstract class
│   ├── rutor.py               # Rutor parser (no login required)
│   ├── rutracker.py           # Rutracker parser (login required)
│   └── kinozal.py             # Kinozal parser
├── templates/
│   ├── index.html             # Home page (trending, movies, TV)
│   ├── movie.html             # Movie/TV details + torrent player
│   ├── category.html          # Category listing (movies/TV/trending)
│   ├── search.html            # Search page
│   ├── favorites.html         # Favorites folders
│   ├── folder_items.html      # Items in favorite folder
│   └── history.html           # Watch/torrent history
├── static/
│   ├── css/style.css          # Main styles
│   └── img/                   # Cached images
├── data/                       # JSON data files
│   ├── favorites.json         # User favorites
│   ├── search_history.json    # Search history
│   ├── selected_torrents.json # Last selected torrent (single)
│   ├── torrent_cache.json     # Search results cache (1 hour)
│   └── torrent_history.json   # Watch history (last 50)
└── cookies/                    # Tracker cookies (Rutracker, etc.)
```

## Key Configuration (config.py)

```python
TMDB_API_KEY = "your_api_key_here"  # Required
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Optional - for Russian trackers
JACKETT_API_KEY = ""  # Jackett API key
JACKETT_URL = "http://localhost:9117"
RUTRACKER_LOGIN = ""
RUTRACKER_PASS = ""
TOR_PROXY = ""  # "socks5h://127.0.0.1:9050"
```

## API Endpoints

### Content
- `GET /` - Home page (trending, movies, TV)
- `GET /movies` - Movies catalog
- `GET /tv-shows` - TV shows catalog
- `GET /trending` - Trending content
- `GET /search?q=query` - Search
- `GET /movie/<id>` - Movie details
- `GET /tv/<id>` - TV show details

### Torrents
- `GET /api/torrents/search?q=query` - Search torrents (cached)
- `POST /api/torrent/start` - Start streaming (body: `{magnet, title, query}`)
- `GET /api/torrent/status` - Get streaming status
- `POST /api/torrent/stop` - Stop streaming
- `DELETE /api/torrent/cache/clear` - Clear search cache

### Favorites
- `GET /api/favorites/folders` - Get all folders
- `POST /api/favorites/folders` - Create folder
- `POST /api/favorites/add` - Add item to folder
- `DELETE /api/favorites/remove/<id>` - Remove item

### History
- `GET /history` - Watch/torrent history page
- `POST /api/history/add` - Add to watch history
- `DELETE /api/history/remove/<id>` - Remove from history

## Development Conventions

### Code Style
- Python: PEP 8 compliant
- Type hints used throughout (`typing` module)
- OOP patterns (classes for all major components)
- Docstrings for all public methods

### Testing Practices
- Check compilation: `python -m py_compile app.py services/*.py`
- Test imports: `python -c "from app import app; print('OK')"`

### Torrent Streaming Flow
```
1. User clicks "Watch" on movie/TV page
2. Search torrents via /api/torrents/search
3. User selects torrent from list
4. POST /api/torrent/start with magnet link
5. Backend: webtorrent download "magnet" --mpv
6. MPV opens on server, streams video
7. Status polling every 2s via /api/torrent/status
8. Window closes when torrent completes/stops
```

### Caching Strategy
- Search results cached for 1 hour (`CACHE_DURATION = 3600`)
- Cache key: lowercase query string
- Auto-invalidates after 1 hour
- Clear via API or delete `data/torrent_cache.json`

### Data Persistence
- All data stored in JSON files under `data/`
- Favorites: folders with items
- History: last 50 entries
- Selected torrent: single object (last chosen)
- Cache: query → results mapping

## Common Issues

### Port 5000 in use
```bash
pkill -f "python.*app.py"
python app.py
```

### WebTorrent not starting
```bash
# Check installation
./node_modules/.bin/webtorrent --version

# Check logs
tail -f /tmp/webtorrent.log

# Restart
pkill -f webtorrent
pkill -f mpv
```

### TMDB API errors
```bash
# Check connectivity
curl http://localhost:5000/api/diagnostics

# Check DNS
nslookup api.themoviedb.org
```

### Cache issues
```bash
# Clear cache
rm data/torrent_cache.json
# Or via API
curl -X DELETE http://localhost:5000/api/torrent/cache/clear
```

## File Purposes Summary

| File | Purpose |
|------|---------|
| `app.py` | Flask app factory, all routes |
| `config.py` | API keys, tracker credentials |
| `torrent_search.py` | Multi-tracker search logic |
| `services/tmdb_client.py` | TMDB API wrapper |
| `services/torrent_manager.py` | Search cache, streaming |
| `services/data_manager.py` | Favorites/history persistence |
| `services/media_formatter.py` | Format TMDB data |
| `parsers/*.py` | Russian tracker spiders |
| `templates/movie.html` | Details page + torrent player UI |
| `templates/history.html` | Watch/torrent history |

## Recent Changes

- ✅ OOP refactoring completed (services layer)
- ✅ Torrent caching implemented (1 hour TTL)
- ✅ Last selected torrent prioritization
- ✅ Torrent history with clean titles
- ✅ History page displays as movie cards
- ✅ Click history item → search results page
- ✅ WebTorrent streaming via `download` command
- ✅ Process verification after start
