"""
NnmClub spider - Russian torrent tracker
"""

import re
import os
import tempfile
from typing import List, Optional, Dict
from bs4 import BeautifulSoup
from . import BaseSpider, SearchResult


class NnmClubSpider(BaseSpider):
    """Spider for nnmclub.to"""

    BASE_URL = "https://nnmclub.to/forum/"
    BASE_URL_TOR = (
        "http://nnmclub2vvjqzjne6q4rrozkkkdmlvnrcsyes2bbkm7e5ut2aproy4id.onion/forum/"
    )
    USE_TOR = True

    PAGE_SIZE = 50

    # Forum categories for movies and TV shows
    FORUM_KEYS = [
        218,  # Зарубежные Новинки (HD*Rip/LQ, DVDRip)
        225,  # Зарубежные Фильмы (HD*Rip/LQ, DVDRip, SATRip, VHSRip)
        319,  # Зарубежная Классика (HD*Rip/LQ, DVDRip, SATRip, VHSRip)
        768,  # Зарубежные сериалы
        231,  # Зарубежные мультфильмы
        232,  # Зарубежные мультсериалы
        1293,  # новинки, но с рекламой (лучше это чем ничего)
    ]

    def __init__(
        self, login: str = None, password: str = None, tor_proxy: Optional[str] = None
    ):
        super().__init__(tor_proxy)
        self.login_str = login
        self.password = password

        # Try to load cookies from cookies folder first
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cookie_file = os.path.join(project_dir, "cookies", "nnmclub_cookies.json")

        if os.path.exists(cookie_file):
            from . import load_cookies_from_file

            cookies = load_cookies_from_file(cookie_file)
            if cookies:
                self.session.cookies.update(cookies)
                print(f"[NnmClub] Loaded {len(cookies)} cookies from {cookie_file}")
        else:
            # Fallback to legacy cookie file
            legacy_cookie_file = os.path.join(
                tempfile.gettempdir(), "nnmclub.cookies.json"
            )
            self.load_cookies(legacy_cookie_file)

        # Store credentials in config if not provided
        if not self.login_str or not self.password:
            try:
                from config import NNMCLUB_LOGIN, NNMCLUB_PASS

                self.login_str = NNMCLUB_LOGIN
                self.password = NNMCLUB_PASS
            except ImportError:
                pass

    def get_name(self) -> str:
        return "NnmClub"

    def is_logged_in(self, html: str) -> bool:
        """Check if user is logged in by looking for logout link or username"""
        # Check for logout link (indicates logged in)
        if 'href="login.php?logout=1"' in html or 'title="Выход"' in html:
            return True
        # Check for username if provided
        if self.login_str and self.login_str in html:
            return True
        # Check for user profile link
        if 'href="profile.php?mode=viewprofile' in html:
            return True
        return False

    def login(self) -> bool:
        """Login to NnmClub using credentials or verify cookies are valid"""
        # If we have cookies loaded, try to verify they're still valid
        if len(self.session.cookies) > 0:
            try:
                print("[NnmClub] Checking if existing cookies are valid...")
                resp = self.get("index.php")
                if self.is_logged_in(resp.text):
                    print("[NnmClub] Cookies are valid, already logged in")
                    return True
                else:
                    print("[NnmClub] Cookies expired or invalid")
            except Exception as e:
                print(f"[NnmClub] Error checking cookies: {e}")

        # If no credentials provided, can't login
        if not self.login_str or not self.password:
            print("[NnmClub] No login credentials provided and no valid cookies")
            return False

        try:
            print(f"[NnmClub] Logging in as {self.login_str}...")

            # First get login page
            resp = self.get("login.php")
            soup = BeautifulSoup(resp.text, "lxml")

            # Find form
            form = soup.find("form", action=re.compile(r"login\.php"))
            if not form:
                print("[NnmClub] Login form not found")
                return False

            # Submit login
            resp = self.post(
                "login.php",
                data={
                    "username": self.login_str,
                    "password": self.password,
                    "login": "Вход",
                },
            )

            if self.is_logged_in(resp.text):
                print("[NnmClub] Login successful")
                # Save cookies to file for future use
                project_dir = os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
                cookie_file = os.path.join(
                    project_dir, "cookies", "nnmclub_cookies.json"
                )
                self.save_cookies_to_file(cookie_file)
                return True
            else:
                print("[NnmClub] Login failed")
                return False
        except Exception as e:
            print(f"[NnmClub] Login error: {e}")
            return False

    def save_cookies_to_file(self, cookie_file: str):
        """Save cookies to JSON file"""
        try:
            import json

            cookies_list = []
            for cookie in self.session.cookies:
                cookies_list.append(
                    {
                        "name": cookie.name,
                        "value": cookie.value,
                        "domain": cookie.domain,
                        "path": cookie.path,
                    }
                )
            with open(cookie_file, "w", encoding="utf-8") as f:
                json.dump(cookies_list, f, indent=2)
            print(f"[NnmClub] Saved {len(cookies_list)} cookies to {cookie_file}")
        except Exception as e:
            print(f"[NnmClub] Error saving cookies: {e}")

    def search(self, query: str) -> List[SearchResult]:
        """Search torrents by query"""
        results = []

        try:
            print(f"[NnmClub] Starting search for: '{query}'")
            print(f"[NnmClub] Cookies in session: {len(self.session.cookies)}")

            # Search via tracker.php
            search_url = "tracker.php"
            data = {"nm": query}  # Simple search without forum filter

            print(f"[NnmClub] Sending POST request to: {search_url}")
            resp = self.post(search_url, data=data)
            html = resp.text
            print(f"[NnmClub] Response status: {resp.status_code}")
            print(f"[NnmClub] Response length: {len(html)} chars")

            # Check if logged in
            is_auth = self.is_logged_in(html)
            print(f"[NnmClub] is_logged_in check: {is_auth}")

            if not is_auth:
                print("[NnmClub] Not logged in, trying to login...")
                if not self.login():
                    print("[NnmClub] Login failed, cannot search")
                    return results
                # Retry search after login
                print("[NnmClub] Retrying search after login...")
                resp = self.post(search_url, data=data)
                html = resp.text

            # Check if no results
            if "Нет записей" in html or "не найдено" in html.lower():
                print("[NnmClub] No results found")
                return results

            soup = BeautifulSoup(html, "lxml")

            # Find results - look for table with topic links
            # Results are usually in a table with class "forumline" or similar
            all_tables = soup.find_all("table")
            print(f"[NnmClub] Found {len(all_tables)} tables")

            # Look for the table that contains viewtopic links
            results_table = None
            for table in all_tables:
                topic_links = table.find_all(
                    "a", href=re.compile(r"viewtopic\.php\?t=")
                )
                if len(topic_links) > 5:  # Results table should have many topic links
                    results_table = table
                    break

            if not results_table:
                print("[NnmClub] ERROR: No results table found")
                return results

            print(f"[NnmClub] Found results table with topics")

            # Parse topics - first get basic info
            topics = []
            for link in results_table.find_all(
                "a", href=re.compile(r"viewtopic\.php\?t=")
            ):
                try:
                    href = link.get("href", "")
                    match = re.search(r"t=(\d+)", href)
                    if not match:
                        continue

                    topic_id = match.group(1)
                    title = link.get_text(strip=True)

                    if not title or title in ["FAQ", "Правила", "Правила оформления"]:
                        continue

                    # Try to find seeds in the same row
                    row = link.find_parent("tr")
                    seeds = 0
                    leechers = 0

                    if row:
                        seed_span = row.find("span", class_="seedmed")
                        leech_span = row.find("span", class_="leechmed")

                        if seed_span:
                            seeds = self.clean_number(seed_span.get_text())
                        if leech_span:
                            leechers = self.clean_number(leech_span.get_text())

                    topics.append(
                        {
                            "topic_id": topic_id,
                            "title": title,
                            "seeds": seeds,
                            "leechers": leechers,
                        }
                    )
                except Exception as e:
                    continue

            print(f"[NnmClub] Found {len(topics)} topics, fetching magnets...")

            # Fetch magnets for each topic (limit to top 15)
            from concurrent.futures import ThreadPoolExecutor, as_completed

            def fetch_magnet(topic_info):
                try:
                    magnet = self.get_magnet_from_topic(topic_info["topic_id"])
                    if magnet:
                        return SearchResult(
                            title=topic_info["title"],
                            magnet=magnet,
                            tracker="NnmClub",
                            seeds=topic_info["seeds"],
                            peers=topic_info["seeds"] + topic_info["leechers"],
                        )
                except Exception as e:
                    pass
                return None

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(fetch_magnet, topic): topic for topic in topics[:15]
                }
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        results.append(result)

            print(f"[NnmClub] Found {len(results)} results with magnets for '{query}'")

        except Exception as e:
            print(f"[NnmClub] Search error: {e}")
            import traceback

            traceback.print_exc()

        return results

    def get_magnet_from_topic(self, topic_id: str) -> Optional[str]:
        """Get magnet link from topic page"""
        try:
            resp = self.get("viewtopic.php", params={"t": topic_id})
            html = resp.text

            # Extract magnet link from HTML
            match = re.search(r'href="(magnet:[^"]+)"', html)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            return None
