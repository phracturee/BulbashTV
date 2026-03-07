"""
Rutracker spider - Russian torrent tracker
"""

import re
import os
import tempfile
from typing import List, Optional, Dict
from bs4 import BeautifulSoup
from urllib.parse import quote
from . import BaseSpider, SearchResult


class RutrackerSpider(BaseSpider):
    """Spider for rutracker.org"""

    BASE_URL = "https://rutracker.org/forum/"
    BASE_URL_TOR = (
        "http://torrentsru5dbmqszbdinnz7cjiubxsjngq52qij6ih3fmp3gn7hwqqd.onion/forum/"
    )
    USE_TOR = False  # Tor site is dead now according to PHP code

    PAGE_SIZE = 50

    # Forum categories for movies and TV shows
    FORUM_KEYS = [
        7,  # Зарубежное кино
        313,  # Зарубежное кино HD
        189,  # Зарубежные сериалы
        2366,  # Зарубежные сериалы HD
        209,  # Зарубежные мультфильмы
        930,  # Зарубежные мультфильмы HD
        815,  # Зарубежные мультсериалы
        1460,  # Зарубежные мультсериалы HD
    ]

    # Blacklisted forums (categories to skip)
    BLACKLISTED_FORUMS = [
        505,  # Индийское кино
        1235,  # Грайндхаус
        2459,  # короткометражки
        212,  # Сборники фильмов
        1640,  # подборки ссылок
        185,  # Звуковые дорожки
        254,  # список актеров
        771,  # список режиссеров
        906,  # ищу звук
        69,  # архив
        44,  # обсуждение
        195,  # некондиционные сериалы
        190,  # архив сериалов
        1147,  # обсуждение сериалов
    ]

    def __init__(self, login: str = None, password: str = None, tor_proxy: Optional[str] = None):
        super().__init__(tor_proxy)
        self.login_str = login
        self.password = password

        # Load cookies from cookies folder
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cookie_file = os.path.join(project_dir, "cookies", "rutracker_cookies.json")

        if os.path.exists(cookie_file):
            from . import load_cookies_from_file

            cookies = load_cookies_from_file(cookie_file)
            if cookies:
                self.session.cookies.update(cookies)
                print(f"[Rutracker] Loaded {len(cookies)} cookies from {cookie_file}")
        else:
            print(f"[Rutracker] No cookies found at {cookie_file}")
            print(f"[Rutracker] Please login to rutracker.org and export cookies to {cookie_file}")

    def _get_next_page_url(self, html: str, current_page: int) -> Optional[str]:
        """Get URL of next page from pagination"""
        try:
            soup = BeautifulSoup(html, "lxml")
            
            # Find pagination links
            # Look for links like: <a class="pg" href="tracker.php?start=50">3</a>
            next_page_num = current_page + 1
            next_start = next_page_num * self.PAGE_SIZE
            
            # Try to find next page link
            pagination = soup.find("div", class_="pagination")
            if pagination:
                for link in pagination.find_all("a", class_="pg"):
                    href = link.get("href", "")
                    if f"start={next_start}" in href:
                        # Found next page
                        if href.startswith("http"):
                            return href
                        return f"{self.BASE_URL}{href}"
            
            # Alternative: find any page link with next start value
            for link in soup.find_all("a", class_="pg"):
                href = link.get("href", "")
                if f"start={next_start}" in href:
                    if href.startswith("http"):
                        return href
                    return f"{self.BASE_URL}{href}"
            
            return None
            
        except Exception as e:
            print(f"[Rutracker] Error getting next page URL: {e}")
            return None

    def get_name(self) -> str:
        return "Rutracker"

    def is_logged_in(self, html: str) -> bool:
        """Check if user is logged in by looking for logout link or username"""
        # Check for logout link (indicates logged in)
        if 'href="logout.php"' in html or 'title="Выход"' in html:
            return True
        # Check for username if provided
        if self.login_str and self.login_str in html:
            return True
        # Check for profile link (logged in users have profile)
        if 'href="profile.php?mode=viewprofile' in html:
            return True
        return False

    def login(self) -> bool:
        """Login to Rutracker using credentials or verify cookies are valid"""
        # If we have cookies loaded, try to verify they're still valid
        if len(self.session.cookies) > 0:
            try:
                print("[Rutracker] Checking if existing cookies are valid...")
                resp = self.get("index.php")
                if self.is_logged_in(resp.text):
                    print("[Rutracker] Cookies are valid, already logged in")
                    return True
                else:
                    print("[Rutracker] Cookies expired or invalid")
            except Exception as e:
                print(f"[Rutracker] Error checking cookies: {e}")

        # If no credentials provided, can't login
        if not self.login_str or not self.password:
            print("[Rutracker] No login credentials provided and no valid cookies")
            return False

        try:
            print(f"[Rutracker] Logging in as {self.login_str}...")
            resp = self.post(
                "login.php",
                data={
                    "login_username": self.login_str,
                    "login_password": self.password,
                    "login": "вход",
                },
            )

            if self.is_logged_in(resp.text):
                print("[Rutracker] Login successful")
                # Save cookies to file for future use
                project_dir = os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__))
                )
                cookie_file = os.path.join(
                    project_dir, "cookies", "rutracker_cookies.json"
                )
                self.save_cookies_to_file(cookie_file)
                return True
            else:
                print("[Rutracker] Login failed")
                return False
        except Exception as e:
            print(f"[Rutracker] Login error: {e}")
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
            print(f"[Rutracker] Saved {len(cookies_list)} cookies to {cookie_file}")
        except Exception as e:
            print(f"[Rutracker] Error saving cookies: {e}")

    def search(self, query: str, max_pages: int = 10) -> List[SearchResult]:
        """Search torrents by query with pagination"""
        results = []

        try:
            print(f"[Rutracker] Starting search for: '{query}'")
            print(f"[Rutracker] Cookies in session: {len(self.session.cookies)}")

            # Try search via tracker.php
            # Note: Don't use forum filter as it breaks cyrillic search
            search_url = "tracker.php"
            params = {
                "nm": query,
                # Forum filter disabled - causes issues with cyrillic queries
                # "f[]": self.FORUM_KEYS,
            }

            print(f"[Rutracker] Sending request to: {search_url}")
            resp = self.get(search_url, params=params)
            html = resp.text
            print(f"[Rutracker] Response status: {resp.status_code}")
            print(f"[Rutracker] Response length: {len(html)} chars")

            # Check if logged in
            is_auth = self.is_logged_in(html)
            print(f"[Rutracker] is_logged_in check: {is_auth}")

            if not is_auth:
                print("[Rutracker] Not logged in, trying to login...")
                if not self.login():
                    print("[Rutracker] Login failed, cannot search")
                    return results
                # Retry search after login
                print("[Rutracker] Retrying search after login...")
                resp = self.get(search_url, params=params)
                html = resp.text

            # Parse all pages
            page = 0
            while page < max_pages:
                print(f"[Rutracker] Parsing page {page + 1}")
                
                soup = BeautifulSoup(html, "lxml")

                # Find results table
                table = soup.find("table", {"id": "tor-tbl"})
                if not table:
                    print(f"[Rutracker] ERROR: No results table found (tor-tbl) on page {page + 1}")
                    if page == 0:
                        print(f"[Rutracker] HTML contains 'tor-tbl': {'tor-tbl' in html}")
                        # Try to find any table
                        all_tables = soup.find_all("table")
                        print(f"[Rutracker] Found {len(all_tables)} tables in HTML")
                    break

                # Parse each row - first pass: get basic info
                page_results = self._parse_results_table(table)
                results.extend(page_results)
                
                print(f"[Rutracker] Found {len(page_results)} results on page {page + 1}")
                
                # Check if there are more pages
                if len(page_results) < self.PAGE_SIZE:
                    print(f"[Rutracker] Last page (only {len(page_results)} results)")
                    break
                
                # Find next page link
                next_page = self._get_next_page_url(html, page)
                if not next_page:
                    print(f"[Rutracker] No more pages found")
                    break
                
                # Load next page
                print(f"[Rutracker] Loading next page: {next_page}")
                resp = self.get(next_page)
                html = resp.text
                page += 1

            print(f"[Rutracker] Total results: {len(results)}")
            
        except Exception as e:
            print(f"[Rutracker] Search error: {e}")
            import traceback
            traceback.print_exc()

        return results

    def _parse_results_table(self, table) -> List[SearchResult]:
        """Parse results table and return list of SearchResult"""
        results = []
        
        # Parse each row - first pass: get basic info
        topics = []
        for row in table.find_all("tr", class_=["tCenter", "hl-tr"]):
            try:
                # Get title and link
                title_link = row.find("a", class_=["tLink", "med"])
                if not title_link:
                    continue

                title = title_link.get_text(strip=True)
                href = title_link.get("href", "")

                # Extract topic ID
                topic_match = re.search(r"t=(\d+)", href)
                if not topic_match:
                    continue
                topic_id = topic_match.group(1)

                # Get seeds/leech - try multiple class names
                seeds = 0
                leechers = 0

                # Try seedmed/leechmed first
                seed_tag = row.find("span", class_="seedmed")
                leech_tag = row.find("span", class_="leechmed")

                # Fallback to seed/leech
                if not seed_tag:
                    seed_tag = row.find("span", class_="seed")
                if not leech_tag:
                    leech_tag = row.find("span", class_="leech")

                # Fallback to b tags
                if not seed_tag:
                    seed_b = row.find("b", string=lambda t: t and "seed" in t.lower())
                    if seed_b:
                        seeds = self.clean_number(seed_b.get_text())

                if not leech_tag:
                    leech_b = row.find("b", string=lambda t: t and "leech" in t.lower())
                    if leech_b:
                        leechers = self.clean_number(leech_b.get_text())

                if seed_tag:
                    seeds = self.clean_number(seed_tag.get_text())
                if leech_tag:
                    leechers = self.clean_number(leech_tag.get_text())

                # Get size
                size_tag = row.find("td", class_="tor-size")
                size = size_tag.get_text(strip=True) if size_tag else ""

                # Extract year from title
                year = self.extract_year(title)

                # Detect quality
                quality = self.detect_quality(title)

                topics.append(
                    {
                        "topic_id": topic_id,
                        "title": title,
                        "seeds": seeds,
                        "leechers": leechers,
                        "size": size,
                        "year": year,
                        "quality": quality,
                    }
                )

            except Exception as e:
                print(f"[Rutracker] Error parsing row: {e}")
                continue

        print(f"[Rutracker] Found {len(topics)} topics, fetching magnets...")

        # Second pass: fetch magnets for each topic (limit to top 50 for more results)
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def fetch_magnet(topic_info):
            try:
                magnet = self.get_magnet_from_topic(topic_info["topic_id"])
                if magnet:
                    return SearchResult(
                        title=topic_info["title"],
                        magnet=magnet,
                        tracker="Rutracker",
                        size=topic_info["size"],
                        seeds=topic_info["seeds"],
                        peers=topic_info["seeds"] + topic_info["leechers"],
                        year=topic_info["year"],
                        quality=topic_info["quality"],
                    )
            except Exception as e:
                print(
                    f"[Rutracker] Error fetching magnet for {topic_info['topic_id']}: {e}"
                )
            return None

        # Fetch magnets in parallel (max 5 workers to avoid being blocked)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(fetch_magnet, topic): topic for topic in topics[:50]
            }
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        print(
            f"[Rutracker] Found {len(results)} results with magnets"
        )

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
            print(f"[Rutracker] Error getting magnet for topic {topic_id}: {e}")
            return None

    def get_topic_details(self, topic_id: str) -> Optional[Dict]:
        """Get detailed info about a topic"""
        try:
            resp = self.get("viewtopic.php", params={"t": topic_id})
            html = resp.text

            soup = BeautifulSoup(html, "lxml")

            # Check if topic exists
            if "Тема не найдена" in html:
                return None

            # Get title
            title_tag = soup.find("h1", class_="maintitle")
            if title_tag:
                title = title_tag.get_text(strip=True)
            else:
                title = "Unknown"

            # Get first post
            post = soup.find("tbody", class_="row1")
            if not post:
                return None

            # Find magnet link
            magnet = None
            attach_block = post.find("fieldset", class_="attach") or post.find(
                "table", class_="attach"
            )
            if attach_block:
                magnet = self.extract_magnet(str(attach_block))

            # Get seeds/leech from post
            seed_tag = soup.find("span", class_="seed")
            leech_tag = soup.find("span", class_="leech")

            seeds = 0
            if seed_tag and seed_tag.find("b"):
                seeds = self.clean_number(seed_tag.find("b").get_text())

            leechers = 0
            if leech_tag and leech_tag.find("b"):
                leechers = self.clean_number(leech_tag.find("b").get_text())

            return {
                "title": title,
                "magnet": magnet,
                "seeds": seeds,
                "leechers": leechers,
            }

        except Exception as e:
            print(f"[Rutracker] Error getting topic {topic_id}: {e}")
            return None
