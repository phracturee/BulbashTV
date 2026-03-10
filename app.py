"""
BulbashTV - Flask web application for movie/TV show discovery and torrent streaming
"""

import os
import socket
import time
import uuid
import logging
from flask import Flask, render_template, jsonify, request
from urllib.parse import unquote

from config import TMDB_API_KEY, TMDB_BASE_URL
from torrent_search import TorrentSearcher
from services.tmdb_client import TMDBClient
from services.data_manager import FavoritesManager, HistoryManager
from services.media_formatter import MediaFormatter, ImageCache
from services.torrent_manager import TorrentManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BulbashTV')


class BulbashTVApp:
    """Main application class"""

    def __init__(self):
        self.app = Flask(__name__)
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_dir = os.path.join(self.project_dir, "data")
        self.static_dir = os.path.join(self.project_dir, "static")

        # Initialize services
        self.tmdb_client = TMDBClient()
        self.favorites_manager = FavoritesManager(self.data_dir)
        self.history_manager = HistoryManager(self.data_dir)
        self.image_cache = ImageCache(self.static_dir)
        self.media_formatter = MediaFormatter(self.image_cache, self.favorites_manager)
        self.torrent_manager = TorrentManager(self.project_dir)

        # Register routes
        self.register_routes()

    def register_routes(self):
        """Register all application routes"""
        # Main pages
        self.app.route("/")(self.home)
        self.app.route("/movies")(self.movies_page)
        self.app.route("/tv-shows")(self.tv_shows_page)
        self.app.route("/trending")(self.trending_page)
        self.app.route("/search")(self.search_page)
        self.app.route("/favorites")(self.favorites_page)
        self.app.route("/favorites/<folder_id>")(self.favorites_folder_page)
        self.app.route("/history")(self.history_page)
        self.app.route("/movie/<int:movie_id>")(self.movie_details)
        self.app.route("/tv/<int:tv_id>")(self.tv_details)
        self.app.route("/tv/<int:tv_id>/episodes")(self.tv_episodes_page)

        # API routes - Movies
        self.app.route("/api/movies")(self.api_movies)
        self.app.route("/api/diagnostics")(self.api_diagnostics)

        # API routes - TV Shows
        self.app.route("/api/tv-shows")(self.api_tv_shows)
        self.app.route("/api/tv/<int:tv_id>/seasons")(self.api_tv_seasons)
        self.app.route("/api/tv/<int:tv_id>/season/<int:season_num>/episodes")(self.api_season_episodes)

        # API routes - Trending
        self.app.route("/api/trending")(self.api_trending)

        # API routes - Search
        self.app.route("/api/search")(self.api_search)
        self.app.route("/api/search/history/clear", methods=["DELETE"])(
            self.clear_search_history_api
        )
        self.app.route("/api/search/history/<query>", methods=["DELETE"])(
            self.delete_search_history_item
        )

        # API routes - Favorites
        self.app.route("/api/favorites/folders", methods=["GET"])(self.get_folders)
        self.app.route("/api/favorites/folders/<folder_id>", methods=["DELETE"])(
            self.delete_folder
        )
        self.app.route("/api/favorites/folders/<folder_id>", methods=["PUT"])(
            self.rename_folder_api
        )
        self.app.route("/api/favorites/folders", methods=["POST"])(self.create_folder)
        self.app.route("/api/favorites/add", methods=["POST"])(self.add_to_favorites)
        self.app.route("/api/favorites/remove/<int:item_id>", methods=["DELETE"])(
            self.remove_from_favorites
        )
        self.app.route("/api/favorites/check/<int:item_id>")(self.check_favorite)

        # API routes - History
        self.app.route("/api/history/add", methods=["POST"])(self.add_to_history)
        self.app.route("/api/history/remove/<int:item_id>", methods=["DELETE"])(
            self.remove_from_history
        )

        # API routes - Torrents
        self.app.route("/api/torrents/search")(self.search_torrents)
        self.app.route("/api/torrents/search/yts")(self.search_torrents_yts)
        self.app.route("/api/torrents/search/tpb")(self.search_torrents_tpb)
        self.app.route("/api/torrents/search/1337x")(self.search_torrents_1337x)
        self.app.route("/api/torrents/search/rutracker")(
            self.search_torrents_rutracker
        )
        self.app.route("/api/torrents/search/lostfilm")(
            self.search_torrents_lostfilm
        )
        self.app.route("/api/torrents/search/series")(
            self.search_series
        )
        self.app.route("/api/lostfilm/magnet")(self.get_lostfilm_magnet)
        self.app.route("/api/torrent/start", methods=["POST"])(self.start_torrent)
        self.app.route("/api/torrent/status")(self.torrent_status)
        self.app.route("/api/torrent/stop", methods=["POST"])(self.stop_torrent)
        self.app.route("/api/torrent/files")(self.get_torrent_files)
        self.app.route("/api/torrent/play", methods=["POST"])(self.play_torrent)
        self.app.route("/api/torrent/history")(self.get_torrent_history)
        self.app.route("/api/torrent/cache/clear", methods=["DELETE"])(self.clear_torrent_cache)
        self.app.route("/api/torrent/progress/save", methods=["POST"])(self.save_playback_progress)
        self.app.route("/api/torrent/progress", methods=["GET"])(self.get_playback_progress)

        # API routes - Misc
        self.app.route("/api/log", methods=["POST"])(self.api_log)

    def run(self, host="0.0.0.0", port=5000, debug=False):
        """Run the application"""
        self.app.run(host=host, port=port, debug=debug)

    # ==================== Page Routes ====================

    def home(self):
        """Home page"""
        # Load more items to compensate for watched ones
        movies_raw = self.tmdb_client.get_movies()[:20]  # Load 20, show 12
        tv_shows_raw = self.tmdb_client.get_tv_shows()[:20]  # Load 20, show 12
        trending_raw = self.tmdb_client.get_trending()[:15]  # Load 15, show 10

        formatted_movies = [self.media_formatter.format_movie(m) for m in movies_raw]
        formatted_tv_shows = [
            self.media_formatter.format_tv_show(s) for s in tv_shows_raw
        ]
        formatted_trending = [
            self.media_formatter.format_trending_item(t, is_main=(i == 0))
            for i, t in enumerate(trending_raw)
        ]

        # Filter out watched items
        formatted_movies = [m for m in formatted_movies if not m.get('is_watched')][:12]
        formatted_tv_shows = [s for s in formatted_tv_shows if not s.get('is_watched')][:12]
        formatted_trending = [t for t in formatted_trending if not t.get('is_watched')][:10]

        return render_template(
            "index.html",
            movies=formatted_movies,
            tv_shows=formatted_tv_shows,
            trending=formatted_trending,
            favorites=self.favorites_manager.to_dict(),
        )

    def movies_page(self):
        """Movies catalog page"""
        genre = request.args.get("genre", "")
        sort_by = request.args.get("sort", "popularity.desc")
        genres = self.tmdb_client.get_genres("movie")

        # Load 3 pages at once (60 items)
        all_movies = []
        for page in range(1, 4):
            movies = self.tmdb_client.get_movies(
                page=page, genre=genre, sort_by=sort_by
            )
            all_movies.extend(movies)

        formatted_movies = [
            self.media_formatter.format_movie(m) for m in all_movies
        ]
        
        # Filter out watched items
        formatted_movies = [m for m in formatted_movies if not m.get('is_watched')]

        return render_template(
            "category.html",
            title="Фильмы",
            items=formatted_movies,
            category="movies",
            genres=genres,
            selected_genre=genre,
            sort_by=sort_by,
            current_page=3,
            favorites=self.favorites_manager.to_dict(),
        )

    def tv_shows_page(self):
        """TV shows catalog page"""
        genre = request.args.get("genre", "")
        sort_by = request.args.get("sort", "popularity.desc")
        genres = self.tmdb_client.get_genres("tv")

        # Load 3 pages at once (60 items)
        all_shows = []
        for page in range(1, 4):
            shows = self.tmdb_client.get_tv_shows(
                page=page, genre=genre, sort_by=sort_by
            )
            all_shows.extend(shows)

        formatted_shows = [self.media_formatter.format_tv_show(s) for s in all_shows]
        
        # Filter out watched items
        formatted_shows = [s for s in formatted_shows if not s.get('is_watched')]

        return render_template(
            "category.html",
            title="Сериалы",
            items=formatted_shows,
            category="tv-shows",
            genres=genres,
            selected_genre=genre,
            sort_by=sort_by,
            current_page=3,
            favorites=self.favorites_manager.to_dict(),
        )

    def trending_page(self):
        """Trending page"""
        # Load 3 pages at once (60 items)
        all_trending = []
        for page in range(1, 4):
            trending = self.tmdb_client.get_trending(
                media_type="all", time_window="week", page=page
            )
            all_trending.extend(trending)

        formatted_trending = [
            self.media_formatter.format_trending_item(t) for t in all_trending
        ]

        return render_template(
            "category.html",
            title="В тренде",
            items=formatted_trending,
            category="trending",
            genres=[],
            selected_genre="",
            sort_by="",
            current_page=3,
            favorites=self.favorites_manager.to_dict(),
        )

    def search_page(self):
        """Search page"""
        query = request.args.get("q", "")
        results = []

        if query:
            search_results = self.tmdb_client.search(query)
            for item in search_results:
                if item.get("media_type") in ["movie", "tv"]:
                    if item["media_type"] == "movie":
                        results.append(self.media_formatter.format_movie(item))
                    else:
                        results.append(self.media_formatter.format_tv_show(item))

            # Add to search history
            self.history_manager.add_search_query(query)

        return render_template(
            "search.html",
            title="Поиск",
            query=query,
            results=results,
            search_history=self.history_manager.search_history_to_dict(),
            favorites=self.favorites_manager.to_dict(),
        )

    def favorites_page(self):
        """Favorites page"""
        return render_template(
            "favorites.html",
            title="Избранное",
            folders=self.favorites_manager.to_dict(),
            favorites=self.favorites_manager.to_dict(),
        )

    def favorites_folder_page(self, folder_id):
        """Page showing items in a specific folder"""
        folder = self.favorites_manager.get_folder(folder_id)
        if not folder:
            return render_template(
                "favorites.html",
                title="Папка не найдена",
                folders=self.favorites_manager.to_dict(),
                error="Папка не найдена",
            )
        return render_template(
            "folder_items.html",
            title=folder.name,
            folder=folder.to_dict(),
            folder_id=folder_id,
            favorites=self.favorites_manager.to_dict(),
        )

    def history_page(self):
        """Watch history page"""
        torrent_history = self.torrent_manager.get_torrent_history()
        
        # Fetch TMDB data for each item to get posters and IDs
        enriched_history = []
        seen_titles = set()  # Track seen titles to avoid duplicates
        
        for item in torrent_history:
            # Skip duplicates
            if item['title'] in seen_titles:
                continue
            seen_titles.add(item['title'])
            
            # Search TMDB for this title
            search_results = self.tmdb_client.search(item['query'], page=1)
            
            poster_path = None
            media_type = 'movie'
            tmdb_id = None
            
            if search_results:
                # Get first result
                first_result = search_results[0]
                poster_path = first_result.get('poster_path')
                media_type = first_result.get('media_type', 'movie')
                tmdb_id = first_result.get('id')
                
                # Add TMDB info to history item
                enriched_item = {
                    **item,
                    'poster_path': poster_path,
                    'media_type': media_type,
                    'tmdb_id': tmdb_id,
                    'url': f"/movie/{tmdb_id}" if media_type == 'movie' else f"/tv/{tmdb_id}",
                }
                enriched_history.append(enriched_item)
            else:
                # No TMDB result, use placeholder
                enriched_history.append({
                    **item,
                    'poster_path': None,
                    'media_type': 'movie',
                    'tmdb_id': None,
                    'url': f"/search?q={item['query']}",  # Fallback to search
                })
        
        return render_template(
            "history.html",
            title="История просмотров",
            torrent_history=enriched_history,
            favorites=self.favorites_manager.to_dict(),
        )

    def movie_details(self, movie_id):
        """Movie details page"""
        movie_data = self.tmdb_client.get_movie_details(movie_id)

        if not movie_data:
            return render_template("404.html", message="Фильм не найден"), 404

        movie = self.media_formatter.format_movie_details(movie_data)

        return render_template(
            "movie.html", item=movie, item_type="movie", favorites=self.favorites_manager.to_dict()
        )

    def tv_details(self, tv_id):
        """TV show details page"""
        tv_data = self.tmdb_client.get_tv_details(tv_id)

        if not tv_data:
            return render_template("404.html", message="Сериал не найден"), 404

        tv_show = self.media_formatter.format_tv_details(tv_data)

        return render_template(
            "movie.html", item=tv_show, item_type="tv", favorites=self.favorites_manager.to_dict()
        )

    def tv_episodes_page(self, tv_id):
        """TV show episodes selection page"""
        tv_data = self.tmdb_client.get_tv_details(tv_id)

        if not tv_data:
            return render_template("404.html", message="Сериал не найден"), 404

        tv_show = self.media_formatter.format_tv_details(tv_data)

        return render_template(
            "tv_episodes.html",
            item=tv_show,
            item_type="tv",
            favorites=self.favorites_manager.to_dict()
        )

    # ==================== API Routes - Movies ====================

    def api_movies(self):
        """API endpoint for movies"""
        page = request.args.get("page", 1, type=int)
        genre = request.args.get("genre", "")
        sort_by = request.args.get("sort", "popularity.desc")

        movies = self.tmdb_client.get_movies(page=page, genre=genre, sort_by=sort_by)
        formatted_movies = [
            self.media_formatter.format_movie(m) for m in movies
        ]

        return jsonify({"items": formatted_movies, "page": page})

    def api_diagnostics(self):
        """Diagnostic endpoint to test connectivity"""
        results = {"timestamp": time.time(), "tests": {}}

        # Test DNS resolution
        try:
            ip = socket.gethostbyname("api.themoviedb.org")
            results["tests"]["dns"] = {"status": "ok", "ip": ip}
        except Exception as e:
            results["tests"]["dns"] = {"status": "error", "error": str(e)}

        # Test TMDB API connection
        try:
            url = f"{TMDB_BASE_URL}/movie/550"
            params = {"api_key": TMDB_API_KEY}
            response = self.tmdb_client.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                results["tests"]["tmdb"] = {
                    "status": "ok",
                    "response_time": response.elapsed.total_seconds(),
                }
            else:
                results["tests"]["tmdb"] = {
                    "status": "error",
                    "code": response.status_code,
                }
        except Exception as e:
            results["tests"]["tmdb"] = {"status": "error", "error": str(e)}

        all_ok = all(t.get("status") == "ok" for t in results["tests"].values())
        results["overall_status"] = "ok" if all_ok else "error"

        return jsonify(results)

    # ==================== API Routes - TV Shows ====================

    def api_tv_shows(self):
        """API endpoint for TV shows"""
        page = request.args.get("page", 1, type=int)
        genre = request.args.get("genre", "")
        sort_by = request.args.get("sort", "popularity.desc")

        shows = self.tmdb_client.get_tv_shows(page=page, genre=genre, sort_by=sort_by)
        formatted_shows = [self.media_formatter.format_tv_show(s) for s in shows]

        return jsonify({"items": formatted_shows, "page": page})

    def api_tv_seasons(self, tv_id):
        """API endpoint for TV show seasons"""
        seasons = self.tmdb_client.get_tv_seasons(tv_id)
        formatted_seasons = [
            self.media_formatter.format_season(s) for s in seasons
        ]

        return jsonify({"seasons": formatted_seasons})

    def api_season_episodes(self, tv_id, season_num):
        """API endpoint for season episodes"""
        episodes = self.tmdb_client.get_season_episodes(tv_id, season_num)
        formatted_episodes = [
            self.media_formatter.format_episode(ep, tv_id, season_num)
            for ep in episodes
        ]

        return jsonify({"episodes": formatted_episodes})

    # ==================== API Routes - Trending ====================

    def api_trending(self):
        """API endpoint for trending"""
        page = request.args.get("page", 1, type=int)

        trending = self.tmdb_client.get_trending(
            media_type="all", time_window="week", page=page
        )
        formatted_trending = [
            self.media_formatter.format_trending_item(t) for t in trending
        ]

        return jsonify({"items": formatted_trending, "page": page})

    # ==================== API Routes - Search ====================

    def api_search(self):
        """API endpoint for search"""
        query = request.args.get("q", "")
        page = request.args.get("page", 1, type=int)

        if not query:
            return jsonify({"items": [], "page": page})

        # Save to search history (only on first page)
        if page == 1:
            self.history_manager.add_search_query(query)

        search_results = self.tmdb_client.search(query, page)

        results = []
        for item in search_results:
            if item.get("media_type") in ["movie", "tv"]:
                if item["media_type"] == "movie":
                    results.append(self.media_formatter.format_movie(item))
                else:
                    results.append(self.media_formatter.format_tv_show(item))

        return jsonify({"items": results, "page": page})

    def clear_search_history_api(self):
        """Clear search history"""
        self.history_manager.clear_search_history()
        return jsonify({"success": True})

    def delete_search_history_item(self, query):
        """Delete individual search history item"""
        decoded_query = unquote(query)
        self.history_manager.remove_search_query(decoded_query)
        return jsonify({"success": True})

    # ==================== API Routes - Favorites ====================

    def get_folders(self):
        """Get all folders"""
        return jsonify(
            {
                "folders": [
                    {"id": k, "name": v["name"], "item_count": len(v["items"])}
                    for k, v in self.favorites_manager.to_dict().items()
                ]
            }
        )

    def delete_folder(self, folder_id):
        """Delete folder"""
        if folder_id == "default":
            return jsonify(
                {"success": False, "message": "Cannot delete default folder"}
            )

        if self.favorites_manager.delete_folder(folder_id):
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Folder not found"})

    def rename_folder_api(self, folder_id):
        """Rename folder"""
        data = request.get_json()
        if data and data.get("name"):
            if self.favorites_manager.rename_folder(folder_id, data["name"]):
                return jsonify({"success": True, "name": data["name"]})
        return jsonify({"success": False, "message": "Name required"})

    def create_folder(self):
        """Create new folder"""
        data = request.get_json()
        if data and data.get("name"):
            folder_id = self.favorites_manager.create_folder(data["name"])
            return jsonify(
                {"success": True, "folder_id": folder_id, "name": data["name"]}
            )
        return jsonify({"success": False, "message": "Name required"})

    def add_to_favorites(self):
        """Add item to favorites folder"""
        data = request.get_json()
        if not data or not data.get("id"):
            return jsonify({"success": False, "message": "Invalid data"})

        folder_id = data.get("folder_id", "default")
        success, message = self.favorites_manager.add_item(folder_id, data)

        if success:
            folder = self.favorites_manager.get_folder(folder_id)
            return jsonify(
                {
                    "success": True,
                    "is_favorite": True,
                    "folder_id": folder_id,
                    "folder_name": folder.name,
                }
            )
        else:
            return jsonify(
                {"success": False, "is_favorite": True, "message": message}
            )

    def remove_from_favorites(self, item_id):
        """Remove item from specific folder or all folders"""
        folder_id = request.args.get("folder_id")
        self.favorites_manager.remove_item(item_id, folder_id)
        return jsonify(
            {"success": True, "is_favorite": self.favorites_manager.is_favorite(item_id)}
        )

    def check_favorite(self, item_id):
        """Check if item is in favorites and return folder list"""
        folders = self.favorites_manager.get_favorite_folders(item_id)
        return jsonify(
            {"is_favorite": len(folders) > 0, "folders": folders}
        )

    # ==================== API Routes - History ====================

    def add_to_history(self):
        """Add item to history"""
        data = request.get_json()
        if data and data.get("id"):
            self.history_manager.add_watch(data)
            return jsonify({"success": True})
        return jsonify({"success": False})

    def remove_from_history(self, item_id):
        """Remove item from history"""
        self.history_manager.remove_watch(item_id)
        return jsonify({"success": True})

    # ==================== API Routes - Torrents ====================

    def search_torrents(self):
        """Search for torrents across multiple trackers"""
        query = request.args.get("q", "")

        if not query:
            return jsonify({"success": False, "message": "No search query provided"})

        try:
            results = self.torrent_manager.search(query)
            # Convert TorrentResult objects to dictionaries
            results_dict = [r.to_dict() if hasattr(r, 'to_dict') else r for r in results]
            return jsonify(
                {
                    "success": True,
                    "query": query,
                    "results": results_dict,
                    "count": len(results_dict),
                }
            )
        except Exception as e:
            print(f"[Search Error] {e}")
            return jsonify({"success": False, "message": str(e)})

    def search_torrents_yts(self):
        """Search YTS only"""
        query = request.args.get("q", "")
        if not query:
            return jsonify({"success": False, "message": "No search query provided"})

        try:
            results = TorrentSearcher.search_yts(query)
            return jsonify(
                {
                    "success": True,
                    "query": query,
                    "results": results,
                    "count": len(results),
                    "tracker": "YTS",
                }
            )
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})

    def search_torrents_tpb(self):
        """Search The Pirate Bay only"""
        query = request.args.get("q", "")
        if not query:
            return jsonify({"success": False, "message": "No search query provided"})

        try:
            results = TorrentSearcher.search_tpb(query)
            return jsonify(
                {
                    "success": True,
                    "query": query,
                    "results": results,
                    "count": len(results),
                    "tracker": "TPB",
                }
            )
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})

    def search_torrents_1337x(self):
        """Search 1337x only"""
        query = request.args.get("q", "")
        if not query:
            return jsonify({"success": False, "message": "No search query provided"})

        try:
            results = TorrentSearcher.search_1337x(query)
            return jsonify(
                {
                    "success": True,
                    "query": query,
                    "results": results,
                    "count": len(results),
                    "tracker": "1337x",
                }
            )
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})

    def search_torrents_rutracker(self):
        """Search RuTracker only"""
        query = request.args.get("q", "")
        if not query:
            return jsonify({"success": False, "message": "No search query provided"})

        try:
            results = TorrentSearcher.search_rutracker(query)
            return jsonify(
                {
                    "success": True,
                    "query": query,
                    "results": results,
                    "count": len(results),
                    "tracker": "RuTracker",
                }
            )
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})

    def search_torrents_lostfilm(self):
        """Search LostFilm only"""
        query = request.args.get("q", "")
        if not query:
            return jsonify({"success": False, "message": "No search query provided"})

        try:
            results = TorrentSearcher.search_lostfilm(query)
            return jsonify(
                {
                    "success": True,
                    "query": query,
                    "results": results,
                    "count": len(results),
                    "tracker": "LostFilm",
                }
            )
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})

    def search_series(self):
        """Search for TV series with specific season"""
        series_name = request.args.get("name", "")
        season = request.args.get("season", 0, type=int)
        
        if not series_name or not season:
            return jsonify({
                "success": False,
                "message": "Series name and season required"
            })

        print(f"\n{'='*60}")
        print(f"[SERIES SEARCH] {'='*60}")
        print(f"[SERIES] Series: {series_name}")
        print(f"[SERIES] Season: {season}")
        print(f"[SERIES] Query: {series_name} Сезон: {season}")
        print(f"[SERIES] {'='*60}")

        try:
            results = self.torrent_manager.search_series(series_name, season)
            
            print(f"[SERIES] Found {len(results)} matching torrents:")
            for i, r in enumerate(results, 1):
                print(f"[SERIES]   [{i}] {r.title}")
                print(f"[SERIES]       Tracker: {r.tracker}")
                print(f"[SERIES]       Seeds: {r.seeds}")
                print(f"[SERIES]       Quality: {r.quality}")
            print(f"[SERIES] {'='*60}\n")
            
            # Convert TorrentResult objects to dictionaries
            results_dict = [r.to_dict() if hasattr(r, 'to_dict') else r for r in results]
            
            return jsonify(
                {
                    "success": True,
                    "series": series_name,
                    "season": season,
                    "results": results_dict,
                    "count": len(results_dict),
                }
            )
        except Exception as e:
            print(f"[SERIES] Error: {e}")
            return jsonify({"success": False, "message": str(e)})

    def get_lostfilm_magnet(self):
        """Get magnet link for LostFilm URL"""
        from parsers.lostfilm import LostFilmSpider
        
        url = request.args.get("url", "")
        if not url:
            return jsonify({"success": False, "message": "No URL provided"})

        try:
            spider = LostFilmSpider()
            magnet = spider.get_movie_download(url)
            
            if magnet:
                return jsonify({"success": True, "magnet": magnet})
            else:
                return jsonify({"success": False, "message": "Failed to get magnet"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})

    def start_torrent(self):
        """Start torrent streaming with popcorn-mpv"""
        data = request.get_json()
        magnet = data.get("magnet") if data else None
        title = data.get("title", "") if data else ""
        query = data.get("query", "") if data else ""

        logger.info(f"Start torrent: magnet={magnet[:50] if magnet else 'None'}..., title={title}")

        success, message, video_url, progress = self.torrent_manager.start_streaming(magnet, title, query)
        
        logger.info(f"Result: success={success}, url={video_url}")
        
        return jsonify({
            "success": success,
            "message": message,
            "video_url": video_url,
            "progress": progress or {},
        })

    def torrent_status(self):
        """Get torrent streaming status"""
        status = self.torrent_manager.get_status()
        
        # Add additional info for frontend
        return jsonify({
            "playing": status.get("playing", False),
            "filename": status.get("filename", ""),
            "time": status.get("time", "0:00"),
            "duration": status.get("duration", "0:00"),
            "progress": status.get("progress", 0),
            "download_speed": status.get("download_speed", "0 MB/s"),
            "peers": status.get("peers", 0),
            "seeds": status.get("seeds", 0),
            "downloaded": status.get("downloaded", "0 MB"),
            "uploaded": status.get("uploaded", "0 MB"),
        })

    def stop_torrent(self):
        """Stop torrent streaming"""
        success = self.torrent_manager.stop_streaming()
        return jsonify({"success": success})

    def get_torrent_files(self):
        """Get list of files in torrent by info hash"""
        info_hash = request.args.get("hash", "")
        
        if not info_hash:
            return jsonify({"success": False, "message": "Info hash required"})
        
        print(f"\n{'='*60}")
        print(f"[TORRENT FILES] {'='*60}")
        print(f"[FILES] Info hash: {info_hash}")
        print(f"[FILES] {'='*60}")
        
        try:
            # For now, return empty list - will be implemented with webtorrent integration
            # This would require querying the webtorrent process for file list
            print(f"[FILES] File list not yet implemented")
            print(f"[FILES] {'='*60}\n")
            
            return jsonify({
                "success": True,
                "files": [],
                "message": "File list not yet implemented"
            })
        except Exception as e:
            print(f"[FILES] Error: {e}")
            return jsonify({"success": False, "message": str(e)})

    def save_playback_progress(self):
        """Save playback position"""
        data = request.get_json()
        magnet = data.get("magnet") if data else None
        position = data.get("position", 0) if data else 0
        duration = data.get("duration", 0) if data else 0
        
        if magnet:
            self.torrent_manager.save_playback_progress(magnet, position, duration)
        
        return jsonify({"success": True})

    def get_playback_progress(self):
        """Get playback progress for a torrent"""
        magnet = request.args.get("magnet", "")
        
        if magnet:
            progress = self.torrent_manager.get_playback_progress(magnet)
            return jsonify(progress)
        
        return jsonify({"position": 0, "duration": 0, "formatted": "0:00"})

    def play_torrent(self):
        """Start playing torrent with mpv"""
        # This is now handled by popcorn-mpv
        return jsonify({"success": True, "message": "Use popcorn-mpv"})

    def get_torrent_history(self):
        """Get torrent history"""
        history = self.torrent_manager.get_torrent_history()
        return jsonify({"history": history})

    def clear_torrent_cache(self):
        """Clear torrent cache"""
        self.torrent_manager.clear_cache()
        return jsonify({"success": True})

    # ==================== API Routes - Misc ====================

    def api_log(self):
        """Log message from client"""
        data = request.get_json()
        if data and "message" in data:
            print(f"[PLAYER] {data['message']}")
        return jsonify({"success": True})


# Create application instance
app_factory = BulbashTVApp()
app = app_factory.app

if __name__ == "__main__":
    app_factory.run(debug=True)
