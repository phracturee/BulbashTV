"""
Base Spider class for torrent parsers
Provides common functionality for all parsers
"""

import re
import json
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Generator
from dataclasses import dataclass
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import os


def load_cookies_from_file(
    cookie_file: str,
) -> Optional[requests.cookies.RequestsCookieJar]:
    """Load cookies from JSON file (Netscape or JSON format)"""
    if not os.path.exists(cookie_file):
        return None

    try:
        with open(cookie_file, "r", encoding="utf-8") as f:
            content = f.read().strip()

        # Try JSON format first
        if content.startswith("[") or content.startswith("{"):
            cookies_data = json.loads(content)

            # Handle array of cookies
            if isinstance(cookies_data, list):
                jar = requests.cookies.RequestsCookieJar()
                for cookie in cookies_data:
                    if isinstance(cookie, dict):
                        name = cookie.get("name") or cookie.get("Name")
                        value = cookie.get("value") or cookie.get("Value")
                        domain = cookie.get("domain") or cookie.get("Domain", "")
                        path = cookie.get("path") or cookie.get("Path", "/")

                        if name and value:
                            jar.set(name, value, domain=domain, path=path)
                return jar

            # Handle dict format {name: value}
            elif isinstance(cookies_data, dict):
                jar = requests.cookies.RequestsCookieJar()
                for name, value in cookies_data.items():
                    jar.set(name, value)
                return jar

        # Try Netscape format
        jar = requests.cookies.RequestsCookieJar()
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split("\t")
            if len(parts) >= 7:
                # Netscape format: domain flag path secure expiry name value
                domain = parts[0]
                path = parts[2]
                secure = parts[3] == "TRUE"
                expires = int(parts[4]) if parts[4].isdigit() else None
                name = parts[5]
                value = parts[6]

                jar.set(name, value, domain=domain, path=path, secure=secure)

        if len(jar):
            return jar

        return None

    except Exception as e:
        print(f"[Cookie Loader] Error loading {cookie_file}: {e}")
        return None


@dataclass
class ForumDto:
    """DTO for forum/category page"""

    id: str
    page: int = 1
    last: Optional[str] = None
    delay: int = 0


@dataclass
class TopicDto:
    """DTO for torrent topic"""

    id: str
    seed: int = 0
    leech: int = 0
    delay: int = 0
    title: str = ""
    magnet: str = ""
    size: str = ""


@dataclass
class SearchResult:
    """DTO for search result"""

    title: str
    magnet: str
    tracker: str
    size: str = ""
    seeds: int = 0
    peers: int = 0
    year: str = ""
    quality: str = ""
    extra: dict = None  # Additional data (for LostFilm URL, etc.)
    
    def __post_init__(self):
        if self.extra is None:
            self.extra = {}


class BaseSpider(ABC):
    """Base class for all torrent spiders"""

    BASE_URL = ""
    BASE_URL_TOR = ""
    USE_TOR = False

    def __init__(self, tor_proxy: Optional[str] = None):
        """Initialize spider with optional Tor proxy"""
        self.session = requests.Session()
        self.tor_proxy = tor_proxy

        # Configure proxy if needed
        if self.USE_TOR and tor_proxy:
            self.session.proxies = {"http": tor_proxy, "https": tor_proxy}

        # Set headers
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            }
        )
        # Note: Not setting Accept-Encoding - requests will handle compression automatically

    @abstractmethod
    def get_name(self) -> str:
        """Return spider name"""
        pass

    @abstractmethod
    def search(self, query: str) -> List[SearchResult]:
        """Search torrents by query"""
        pass

    def get_base_url(self) -> str:
        """Get base URL (Tor or regular)"""
        if self.USE_TOR and self.tor_proxy and self.BASE_URL_TOR:
            return self.BASE_URL_TOR
        return self.BASE_URL

    def get(self, url: str, **kwargs) -> requests.Response:
        """Make GET request"""
        full_url = urljoin(self.get_base_url(), url)
        return self.session.get(full_url, timeout=30 if self.USE_TOR else 30, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        """Make POST request"""
        full_url = urljoin(self.get_base_url(), url)
        return self.session.post(full_url, timeout=30 if self.USE_TOR else 30, **kwargs)

    @staticmethod
    def extract_magnet(html: str) -> Optional[str]:
        """Extract magnet link from HTML"""
        match = re.search(r'"(magnet[^"]+)"', html)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def extract_imdb(html: str) -> Optional[str]:
        """Extract IMDB ID from HTML"""
        # Look for imdb.com/title/tt1234567
        match = re.search(r"imdb\.com/title/(tt\d+)", html)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def detect_quality(title: str) -> str:
        """Detect video quality from title"""
        title_lower = title.lower()

        if "2160p" in title_lower or "4k" in title_lower:
            return "2160p"
        elif "1080p" in title_lower:
            return "1080p"
        elif "720p" in title_lower:
            return "720p"
        elif "480p" in title_lower:
            return "480p"
        elif "bluray" in title_lower:
            return "BluRay"
        elif "web-dl" in title_lower or "webdl" in title_lower:
            return "WEB-DL"
        elif "webrip" in title_lower:
            return "WEB-Rip"
        elif "hdrip" in title_lower:
            return "HD-Rip"
        elif "dvdrip" in title_lower:
            return "DVD-Rip"
        elif "hdtv" in title_lower:
            return "HDTV"
        else:
            return "Unknown"

    @staticmethod
    def clean_number(text: str) -> int:
        """Extract number from text"""
        numbers = re.findall(r"\d+", str(text))
        if numbers:
            return int(numbers[0])
        return 0

    @staticmethod
    def extract_year(title: str) -> str:
        """Extract year from title"""
        match = re.search(r"\((\d{4})\)", title)
        if match:
            return match.group(1)
        match = re.search(r"\[(\d{4})\]", title)
        if match:
            return match.group(1)
        return ""

    def load_cookies(self, cookie_file: str):
        """Load cookies from file"""
        if os.path.exists(cookie_file):
            try:
                with open(cookie_file, "r") as f:
                    cookies = json.load(f)
                    self.session.cookies.update(cookies)
            except Exception as e:
                print(f"Error loading cookies: {e}")

    def save_cookies(self, cookie_file: str):
        """Save cookies to file"""
        try:
            cookies = dict(self.session.cookies)
            with open(cookie_file, "w") as f:
                json.dump(cookies, f)
        except Exception as e:
            print(f"Error saving cookies: {e}")
