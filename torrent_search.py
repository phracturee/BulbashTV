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

    def search_rutor(self, query: str) -> List[TorrentResult]:
        """Search Rutor via Python parser (no login required)"""
        try:
            from parsers.rutor import RutorSpider

            spider = RutorSpider()
            results = spider.search(query)
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

    def search_all(
        self, query: str, trackers: Optional[List[str]] = None
    ) -> List[TorrentResult]:
        """Search all available trackers"""
        if not query:
            return []

        # Default trackers (only RuTracker and Rutor)
        available_trackers = [
            ("RuTracker", self.search_rutracker),
            ("Rutor", self.search_rutor),
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
        with ThreadPoolExecutor(max_workers=2) as executor:
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

        # Sort by seeds (descending)
        results.sort(key=lambda x: x.seeds, reverse=True)

        print(
            f"[Search Complete] Total: {len(results)} results in {time.time() - start_time:.2f}s"
        )
        return results

    def search_single_tracker(
        self, tracker_name: str, query: str
    ) -> List[TorrentResult]:
        """Search single tracker by name"""
        trackers = {
            "RuTracker": self.search_rutracker,
            "Rutor": self.search_rutor,
        }

        if tracker_name not in trackers:
            print(f"Unknown tracker: {tracker_name}")
            return []

        return trackers[tracker_name](query)
