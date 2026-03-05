"""
TMDB API Client with retry logic and caching
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Any, Optional
import time
from datetime import datetime

from config import TMDB_API_KEY, TMDB_BASE_URL


class TMDBClient:
    """Client for The Movie Database API"""

    def __init__(self, api_key: str = TMDB_API_KEY, base_url: str = TMDB_BASE_URL):
        self.api_key = api_key
        self.base_url = base_url
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
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

    def get_movies(
        self, page: int = 1, genre: Optional[str] = None, sort_by: str = "popularity.desc"
    ) -> List[Dict[str, Any]]:
        """Get popular movies from TMDB with filters"""
        url = f"{self.base_url}/discover/movie"
        params = {
            "api_key": self.api_key,
            "language": "ru-RU",
            "page": page,
            "sort_by": sort_by,
            "with_release_type": "2,3,4,5",  # Только вышедшие фильмы
            "primary_release_date.lte": datetime.now().strftime("%Y-%m-%d"),  # Не будущие
        }
        if genre:
            params["with_genres"] = genre

        return self._make_request(url, params)

    def get_tv_shows(
        self, page: int = 1, genre: Optional[str] = None, sort_by: str = "popularity.desc"
    ) -> List[Dict[str, Any]]:
        """Get popular TV shows from TMDB with filters"""
        url = f"{self.base_url}/discover/tv"
        params = {
            "api_key": self.api_key,
            "language": "ru-RU",
            "page": page,
            "sort_by": sort_by,
            "first_air_date.lte": datetime.now().strftime("%Y-%m-%d"),  # Не будущие
        }
        if genre:
            params["with_genres"] = genre

        return self._make_request(url, params)

    def get_trending(
        self, media_type: str = "all", time_window: str = "week", page: int = 1
    ) -> List[Dict[str, Any]]:
        """Get trending movies/TV shows from TMDB"""
        url = f"{self.base_url}/trending/{media_type}/{time_window}"
        params = {
            "api_key": self.api_key,
            "language": "ru-RU",
            "page": page,
        }

        return self._make_request(url, params)

    def search(self, query: str, page: int = 1) -> List[Dict[str, Any]]:
        """Search movies and TV shows from TMDB"""
        url = f"{self.base_url}/search/multi"
        params = {
            "api_key": self.api_key,
            "language": "ru-RU",
            "query": query,
            "page": page,
            "include_adult": "false",
        }

        return self._make_request(url, params)

    def get_genres(self, media_type: str = "movie") -> List[Dict[str, Any]]:
        """Get genres list from TMDB"""
        url = f"{self.base_url}/genre/{media_type}/list"
        params = {"api_key": self.api_key, "language": "ru-RU"}

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json().get("genres", [])
        except Exception as e:
            print(f"Error fetching genres: {e}")
            return []

    def get_movie_details(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed movie information from TMDB with retry logic"""
        url = f"{self.base_url}/movie/{movie_id}"
        params = {
            "api_key": self.api_key,
            "language": "ru-RU",
            "append_to_response": "credits",
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=15)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.ConnectionError as e:
                print(
                    f"[TMDB] Connection error (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))
            except requests.exceptions.Timeout:
                print(f"[TMDB] Timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2 * (attempt + 1))
            except Exception as e:
                print(f"[TMDB] Error: {e}")
                break

        # Return mock data if API fails
        return {
            "id": movie_id,
            "title": "Фильм недоступен",
            "overview": "Не удалось загрузить информацию о фильме.",
            "poster_path": None,
            "backdrop_path": None,
            "release_date": "",
            "genres": [],
            "vote_average": 0,
            "runtime": 0,
            "tagline": "",
        }

    def get_tv_details(self, tv_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed TV show information from TMDB"""
        url = f"{self.base_url}/tv/{tv_id}"
        params = {
            "api_key": self.api_key,
            "language": "ru-RU",
            "append_to_response": "credits",
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching TV details: {e}")
            return None

    def get_tv_seasons(self, tv_id: int) -> List[Dict[str, Any]]:
        """Get list of seasons for a TV show"""
        tv_details = self.get_tv_details(tv_id)
        if not tv_details:
            return []

        seasons = tv_details.get("seasons", [])
        # Filter out special seasons (type: "Special")
        return [s for s in seasons if s.get("season_number", 0) > 0]

    def get_season_episodes(
        self, tv_id: int, season_number: int
    ) -> List[Dict[str, Any]]:
        """Get episodes for a specific season"""
        url = f"{self.base_url}/tv/{tv_id}/season/{season_number}"
        params = {
            "api_key": self.api_key,
            "language": "ru-RU",
        }

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            season_data = response.json()
            return season_data.get("episodes", [])
        except Exception as e:
            print(f"Error fetching season episodes: {e}")
            return []

    def _make_request(
        self, url: str, params: Dict[str, Any], timeout: int = 10
    ) -> List[Dict[str, Any]]:
        """Make HTTP request with error handling"""
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json().get("results", [])
        except Exception as e:
            print(f"Error fetching data: {e}")
            return []
