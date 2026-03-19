"""
Media formatter - formats TMDB data for templates and handles image caching
"""

import os
import requests
from typing import Dict, Any, Optional, List

from config import TMDB_BASE_URL
from services.data_manager import FavoritesManager


class ImageCache:
    """Handle image caching for main movie"""

    def __init__(self, static_dir: str):
        self.static_dir = static_dir
        self.img_dir = os.path.join(static_dir, "img")
        os.makedirs(self.img_dir, exist_ok=True)
        self.main_movie_file = os.path.join(self.img_dir, "main_movie.txt")

    def _create_proxy_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def download_main_movie_image(self, tmdb_path: str) -> Optional[str]:
        """Download main movie image to local cache"""
        if not tmdb_path:
            return None

        filename = tmdb_path.replace("/", "")
        filepath = os.path.join(self.img_dir, filename)

        # Check if we need to update main movie
        current_main = None
        if os.path.exists(self.main_movie_file):
            with open(self.main_movie_file, "r") as f:
                current_main = f.read().strip()

        # If different movie, delete old cache
        if current_main and current_main != filename:
            old_path = os.path.join(self.img_dir, current_main)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except:
                    pass

        # Download if not exists
        if not os.path.exists(filepath):
            try:
                session = self._create_proxy_session()
                url = f"https://image.tmdb.org/t/p/original{tmdb_path}"
                response = session.get(url, timeout=30)
                if response.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    with open(self.main_movie_file, "w") as f:
                        f.write(filename)
                    return f"/static/img/{filename}"
            except Exception as e:
                print(f"Failed to download main movie: {e}")
                return None
        else:
            # Update tracking file
            with open(self.main_movie_file, "w") as f:
                f.write(filename)
            return f"/static/img/{filename}"

        return None

    def get_image_url(
        self, tmdb_path: Optional[str], size: str = "w500", is_main: bool = False
    ) -> Optional[str]:
        """Get image URL - direct TMDB URL"""
        if not tmdb_path:
            return None

        if is_main:
            local = self.download_main_movie_image(tmdb_path)
            if local:
                return local

        # Use direct TMDB URL
        return f"https://image.tmdb.org/t/p/{size}{tmdb_path}"


class MediaFormatter:
    """Format TMDB media data for templates"""

    def __init__(
        self, image_cache: ImageCache, favorites_manager: FavoritesManager
    ):
        self.image_cache = image_cache
        self.favorites_manager = favorites_manager

    def format_movie(
        self, movie: Dict[str, Any], is_main: bool = False
    ) -> Dict[str, Any]:
        """Format movie data for template"""
        movie_id = movie.get("id")
        return {
            "id": movie_id,
            "title": movie.get("title", "Без названия"),
            "overview": movie.get("overview", ""),
            "poster_path": self.image_cache.get_image_url(
                movie.get("poster_path"), "w500", is_main
            ),
            "backdrop_path": self.image_cache.get_image_url(
                movie.get("backdrop_path"), "original", is_main
            ),
            "release_date": movie.get("release_date", "")[:4]
            if movie.get("release_date")
            else "",
            "vote_average": round(movie.get("vote_average", 0), 1),
            "genre_ids": movie.get("genre_ids", []),
            "is_favorite": self.favorites_manager.is_favorite(movie_id),
            "is_watched": self.favorites_manager.is_watched(movie_id),
            "media_type": "Фильм",
            "original_media_type": "movie",
            "url": f"/movie/{movie_id}",
        }

    def format_tv_show(self, show: Dict[str, Any]) -> Dict[str, Any]:
        """Format TV show data for template"""
        show_id = show.get("id")
        
        # Format title: "Russian Name / English Name" if both available
        title = show.get("name", "Без названия")
        original_name = show.get("original_name", "")
        
        # If title is in Russian and we have English original name
        if original_name and title != original_name:
            title = f"{title} / {original_name}"
        
        return {
            "id": show_id,
            "title": title,
            "overview": show.get("overview", ""),
            "poster_path": self.image_cache.get_image_url(
                show.get("poster_path"), "w500"
            ),
            "backdrop_path": self.image_cache.get_image_url(
                show.get("backdrop_path"), "original"
            ),
            "first_air_date": show.get("first_air_date", "")[:4]
            if show.get("first_air_date")
            else "",
            "vote_average": round(show.get("vote_average", 0), 1),
            "genre_ids": show.get("genre_ids", []),
            "is_favorite": self.favorites_manager.is_favorite(show_id),
            "is_watched": self.favorites_manager.is_watched(show_id),
            "media_type": "Сериал",
            "original_media_type": "tv",
            "url": f"/tv/{show_id}",
        }

    def format_trending_item(
        self, item: Dict[str, Any], is_main: bool = False
    ) -> Dict[str, Any]:
        """Format trending item data for template"""
        is_movie = item.get("media_type") == "movie"
        item_id = item.get("id")
        return {
            "id": item_id,
            "title": item.get("title")
            if is_movie
            else item.get("name", "Без названия"),
            "overview": item.get("overview", ""),
            "poster_path": self.image_cache.get_image_url(
                item.get("poster_path"), "w500", is_main
            ),
            "backdrop_path": self.image_cache.get_image_url(
                item.get("backdrop_path"), "original", is_main
            ),
            "release_date": (
                item.get("release_date")
                if is_movie
                else item.get("first_air_date", "")
            )[:4],
            "vote_average": round(item.get("vote_average", 0), 1),
            "media_type": "Фильм" if is_movie else "Сериал",
            "original_media_type": "movie" if is_movie else "tv",
            "url": f"/movie/{item_id}" if is_movie else f"/tv/{item_id}",
            "is_favorite": self.favorites_manager.is_favorite(item_id),
            "is_watched": self.favorites_manager.is_watched(item_id),
        }

    def format_movie_details(
        self, movie_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Format detailed movie data for template"""
        if not movie_data:
            return None

        poster_path_tmdb = movie_data.get("poster_path")
        return {
            "id": movie_data.get("id"),
            "title": movie_data.get("title", "Нет названия"),
            "overview": movie_data.get("overview", ""),
            "poster_path": self.image_cache.get_image_url(poster_path_tmdb),
            "poster_path_original": f"https://image.tmdb.org/t/p/w500{poster_path_tmdb}" if poster_path_tmdb else "",
            "backdrop_path": self.image_cache.get_image_url(
                movie_data.get("backdrop_path"), size="original"
            )
            if movie_data.get("backdrop_path")
            else None,
            "release_date": movie_data.get("release_date", ""),
            "year": movie_data.get("release_date", "")[:4]
            if movie_data.get("release_date")
            else "",
            "genres": [g["name"] for g in movie_data.get("genres", [])],
            "vote_average": round(movie_data.get("vote_average", 0), 1),
            "runtime": movie_data.get("runtime"),
            "tagline": movie_data.get("tagline", ""),
            "is_watched": self.favorites_manager.is_watched(movie_data.get("id")),
        }

    def format_tv_details(
        self, tv_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Format detailed TV show data for template"""
        if not tv_data:
            return None

        poster_path_tmdb = tv_data.get("poster_path")
        return {
            "id": tv_data.get("id"),
            "title": tv_data.get("name", "Нет названия"),
            "overview": tv_data.get("overview", ""),
            "poster_path": self.image_cache.get_image_url(poster_path_tmdb),
            "poster_path_original": f"https://image.tmdb.org/t/p/w500{poster_path_tmdb}" if poster_path_tmdb else "",
            "backdrop_path": self.image_cache.get_image_url(
                tv_data.get("backdrop_path"), size="original"
            )
            if tv_data.get("backdrop_path")
            else None,
            "release_date": tv_data.get("first_air_date", ""),
            "year": tv_data.get("first_air_date", "")[:4]
            if tv_data.get("first_air_date")
            else "",
            "genres": [g["name"] for g in tv_data.get("genres", [])],
            "vote_average": round(tv_data.get("vote_average", 0), 1),
            "number_of_seasons": tv_data.get("number_of_seasons"),
            "number_of_episodes": tv_data.get("number_of_episodes"),
            "tagline": tv_data.get("tagline", ""),
            "seasons": tv_data.get("seasons", []),
            "is_watched": self.favorites_manager.is_watched(tv_data.get("id")),
        }

    def format_season(self, season: Dict[str, Any]) -> Dict[str, Any]:
        """Format season data for template"""
        return {
            "id": season.get("id"),
            "name": season.get("name", f"Сезон {season.get('season_number', 1)}"),
            "season_number": season.get("season_number", 1),
            "episode_count": season.get("episode_count", 0),
            "air_date": season.get("air_date", ""),
            "poster_path": self.image_cache.get_image_url(
                season.get("poster_path"), "w500"
            ),
            "overview": season.get("overview", ""),
        }

    def format_episode(
        self, episode: Dict[str, Any], tv_id: int, season_number: int
    ) -> Dict[str, Any]:
        """Format episode data for template"""
        episode_num = episode.get("episode_number", 1)
        return {
            "id": episode.get("id"),
            "name": episode.get("name", f"Серия {episode_num}"),
            "episode_number": episode_num,
            "season_number": season_number,
            "air_date": episode.get("air_date", ""),
            "overview": episode.get("overview", ""),
            "poster_path": self.image_cache.get_image_url(
                episode.get("still_path"), "w500"
            ),
            "runtime": episode.get("runtime"),
            "vote_average": round(episode.get("vote_average", 0), 1),
            "tv_id": tv_id,
            "search_query": f"S{season_number:02d}E{episode_num:02d} {episode.get('name', '')}",
        }
