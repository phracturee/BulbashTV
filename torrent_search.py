"""
Torrent Searcher - Search for torrents across multiple trackers
"""

import requests
import re
import os
import json
import time
import hashlib
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Callable
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup


class TorrentResult:
    """Data class for torrent search result"""

    def __init__(
        self,
        title: str,
        magnet: str,
        tracker: str,
        size: str = "Unknown",
        seeds: int = 0,
        peers: int = 0,
        year: str = "",
        quality: str = "Unknown",
        torrent_type: str = "movie",
        extra: dict = None,
    ):
        self.title = title
        self.magnet = magnet
        self.tracker = tracker
        self.size = size
        self.seeds = seeds
        self.peers = peers
        self.year = year
        self.quality = quality
        self.type = torrent_type
        self.extra = extra or {}  # Additional data (for LostFilm URL, etc.)
        self.selected = False
        self.selected_at = 0

    def to_dict(self) -> Dict[str, any]:
        return {
            "title": self.title,
            "year": self.year,
            "quality": self.quality,
            "size": self.size,
            "seeds": self.seeds,
            "peers": self.peers,
            "magnet": self.magnet,
            "tracker": self.tracker,
            "type": self.type,
            "selected": self.selected,
            "selected_at": self.selected_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> "TorrentResult":
        result = cls(
            title=data.get("title", "Unknown"),
            magnet=data.get("magnet", ""),
            tracker=data.get("tracker", "Unknown"),
            size=data.get("size", "Unknown"),
            seeds=data.get("seeds", 0),
            peers=data.get("peers", 0),
            year=data.get("year", ""),
            quality=data.get("quality", "Unknown"),
            torrent_type=data.get("type", "movie"),
        )
        result.selected = data.get("selected", False)
        result.selected_at = data.get("selected_at", 0)
        return result


class SelectedTorrentsManager:
    """Manage selected/preferred torrents"""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.file_path = os.path.join(data_dir, "selected_torrents.json")
        os.makedirs(data_dir, exist_ok=True)

    @staticmethod
    def get_torrent_id(magnet: str) -> str:
        """Generate unique ID from magnet link"""
        if not magnet:
            return ""
        match = re.search(r"btih:([a-fA-F0-9]{40})", magnet)
        if match:
            return match.group(1).lower()
        return hashlib.md5(magnet.encode()).hexdigest()

    def load(self) -> Dict[str, any]:
        """Load selected torrents from file"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading selected torrents: {e}")
        return {}

    def save(self, magnet: str, title: str, query: str) -> None:
        """Save selected torrent"""
        try:
            selected = self.load()
            torrent_id = self.get_torrent_id(magnet)

            if torrent_id:
                selected[torrent_id] = {
                    "magnet": magnet,
                    "title": title,
                    "query": query,
                    "timestamp": time.time(),
                }

                with open(self.file_path, "w", encoding="utf-8") as f:
                    json.dump(selected, f, ensure_ascii=False, indent=2)
                print(f"[TorrentSearcher] Saved selected torrent: {title[:50]}...")
        except Exception as e:
            print(f"Error saving selected torrent: {e}")

    def is_selected(self, magnet: str) -> bool:
        """Check if torrent was previously selected"""
        if not magnet:
            return False
        selected = self.load()
        torrent_id = self.get_torrent_id(magnet)
        return torrent_id in selected

    def prioritize_results(
        self, results: List[TorrentResult], query: str
    ) -> List[TorrentResult]:
        """Prioritize selected torrents and mark them"""
        selected = self.load()

        selected_list = []
        unselected_list = []

        for result in results:
            torrent_id = self.get_torrent_id(result.magnet)

            if torrent_id in selected:
                result.selected = True
                result.selected_at = selected[torrent_id].get("timestamp", 0)
                selected_list.append(result)
            else:
                result.selected = False
                unselected_list.append(result)

        # Sort selected by timestamp (newest first)
        selected_list.sort(key=lambda x: x.selected_at, reverse=True)

        return selected_list + unselected_list


class TorrentSearcher:
    """Search for torrents across multiple trackers"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.selected_manager = SelectedTorrentsManager(data_dir)

    # ==================== Quality Detection ====================

    @staticmethod
    def detect_quality(filename: str) -> str:
        """Detect video quality from filename"""
        filename_lower = filename.lower()

        quality_map = [
            ("2160p", "4k", "2160p (4K)"),
            ("1080p", "1080p"),
            ("720p", "720p"),
            ("480p", "480p"),
            ("bluray", "BluRay"),
            ("web-dl", "webdl", "WEB-DL"),
            ("webrip", "WEB-Rip"),
            ("hdrip", "HD-Rip"),
            ("dvdrip", "DVD-Rip"),
            ("hdtv", "HDTV"),
        ]

        for patterns, quality in (
            (patterns[:-1], patterns[-1]) for patterns in quality_map
        ):
            if any(p in filename_lower for p in patterns):
                return quality

        return "Unknown"

    # ==================== Search Methods - Public APIs ====================


    # ==================== Search Methods - Russian Trackers ====================

    def search_rutracker(self, query: str, max_pages: int = 10) -> List[TorrentResult]:
        """Search RuTracker via Python parser with pagination (uses cookies)"""
        try:
            from parsers.rutracker import RutrackerSpider

            spider = RutrackerSpider()
            results = spider.search(query, max_pages=max_pages)
            return [
                TorrentResult(
                    title=r.title,
                    year=r.year,
                    quality=r.quality,
                    size=r.size,
                    seeds=r.seeds,
                    peers=r.peers,
                    magnet=r.magnet,
                    tracker=r.tracker,
                    torrent_type="movie",
                )
                for r in results
            ]
        except Exception as e:
            print(f"RuTracker search error: {e}")
            return []

    def search_rutor(self, query: str, max_pages: int = 5) -> List[TorrentResult]:
        """Search Rutor via Python parser with pagination"""
        try:
            from parsers.rutor import RutorSpider

            spider = RutorSpider()
            results = spider.search(query, max_pages=max_pages)
            return [
                TorrentResult(
                    title=r.title,
                    year=r.year,
                    quality=r.quality,
                    size=r.size,
                    seeds=r.seeds,
                    peers=r.peers,
                    magnet=r.magnet,
                    tracker=r.tracker,
                    torrent_type="movie",
                )
                for r in results
            ]
        except Exception as e:
            print(f"Rutor search error: {e}")
            return []

    def search_lostfilm(self, query: str) -> List[TorrentResult]:
        """Search LostFilm via parser - show results immediately, get magnet on selection"""
        try:
            from parsers.lostfilm import LostFilmSpider

            spider = LostFilmSpider()
            search_results = spider.search(query)
            
            print(f"[LostFilm] Converting {len(search_results)} search results to TorrentResult")
            
            # Convert search results to TorrentResult - show ALL results immediately
            results = []
            for r in search_results:
                if not r.title:
                    continue
                
                # Use English title for search, but store Russian for display
                display_title = r.extra.get("title_ru", r.title)
                full_title = f"{display_title} ({r.year})" if r.year else display_title
                    
                # Store URL in magnet field, will fetch real magnet on selection
                results.append(
                    TorrentResult(
                        title=full_title,  # Show Russian title with year
                        year=r.year,
                        quality=r.quality,
                        size="",
                        seeds=0,  # LostFilm doesn't show seeds
                        peers=0,
                        magnet=r.magnet or r.extra.get("url", ""),  # URL for now
                        tracker="LostFilm",
                        torrent_type="movie" if r.extra.get("type") == "Фильм" else "tv",
                        extra=r.extra,  # Store extra data for later (includes English title)
                    )
                )
            
            print(f"[LostFilm] Returning {len(results)} results")
            return results
        except Exception as e:
            print(f"LostFilm search error: {e}")
            import traceback
            traceback.print_exc()
            return []

    def search_all(
        self, query: str, trackers: Optional[List[str]] = None
    ) -> List[TorrentResult]:
        """Search all available trackers"""
        if not query:
            return []

        # Default trackers (RuTracker, Rutor, LostFilm)
        available_trackers = [
            ("RuTracker", self.search_rutracker),
            ("Rutor", self.search_rutor),
            ("LostFilm", self.search_lostfilm),
        ]

        # Filter if specific trackers requested
        if trackers:
            available_trackers = [
                (name, func)
                for name, func in available_trackers
                if name in trackers
            ]

        results = []
        start_time = time.time()

        # Search in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(func, query): name
                for name, func in available_trackers
            }

            for future in as_completed(futures):
                tracker_name = futures[future]
                try:
                    tracker_results = future.result(timeout=30)
                    results.extend(tracker_results)
                    print(
                        f"[{tracker_name}] Found {len(tracker_results)} results in {time.time() - start_time:.2f}s"
                    )
                except Exception as e:
                    print(f"[{tracker_name}] Error: {e}")

        # Sort: first with year in title, then without year, sorted by seeds within each group
        import re
        
        def has_year_in_title(title):
            """Check if title contains a 4-digit year (1900-2099)"""
            return bool(re.search(r'\b(19|20)\d{2}\b', title))
        
        def sort_key(x):
            # Priority 1: Has year in title (1 = has year, 0 = no year)
            has_year = 1 if has_year_in_title(x.title) else 0
            # Priority 2: Number of seeds (descending)
            return (has_year, x.seeds)
        
        results.sort(key=sort_key, reverse=True)

        print(
            f"[Search Complete] Total: {len(results)} results in {time.time() - start_time:.2f}s"
        )
        return results

    def search_series(self, series_name: str, season: int) -> List[TorrentResult]:
        """Search for TV series with specific season"""
        # Format query: "Series Name / Season: X"
        # Try to extract English name if available (format: "Russian / English")
        query = f"{series_name} Сезон: {season}"
        
        # If series name contains both Russian and English (separated by /)
        if '/' in series_name:
            parts = series_name.split('/')
            if len(parts) >= 2:
                # Use format: "Russian / English / Season: X"
                russian_name = parts[0].strip()
                english_name = parts[1].strip()
                query = f"{russian_name} / {english_name} / Сезон: {season}"
        
        print(f"[Series Search] Searching for: {query}")

        # Search RuTracker (best for Russian series)
        try:
            results = self.search_rutracker(query, max_pages=3)

            # Filter results for exact match
            filtered = []
            for r in results:
                if self._is_correct_series(r.title, series_name, season):
                    filtered.append(r)

            print(f"[Series Search] Found {len(filtered)} matching torrents")
            return filtered
        except Exception as e:
            print(f"[Series Search] Error: {e}")
            return []
    
    def _is_correct_series(self, title: str, series_name: str, season: int) -> bool:
        """Check if torrent title matches series and season exactly"""
        import re
        
        # Normalize title
        title_lower = title.lower()
        series_lower = series_name.lower()
        
        # Check if series name matches (exact match, not partial)
        if series_lower not in title_lower:
            return False
        
        # Check season number - must match exactly (not 2 for 22)
        # Look for "Сезон: X" or "Season X" pattern
        season_patterns = [
            rf'сезон:\s*{season}\b',  # Сезон: 2
            rf'сезон\s+{season}\b',   # Сезон 2
            rf'season\s*{season}\b',   # Season 2
            rf's{season:02d}\b',       # S02 or S2
        ]
        
        season_found = False
        for pattern in season_patterns:
            if re.search(pattern, title_lower):
                season_found = True
                break
        
        if not season_found:
            return False
        
        # Make sure it's not a wrong season (e.g., 2 for 22)
        # Check that season number is not part of a larger number
        wrong_seasons = [i for i in range(1, 100) if i != season and str(i) in str(season)]
        for wrong in wrong_seasons:
            if re.search(rf'сезон:\s*{wrong}\b', title_lower):
                return False
        
        return True
