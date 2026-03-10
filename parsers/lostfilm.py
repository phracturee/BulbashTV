"""
LostFilm.tv spider - Russian HD tracker
Requires no login
"""

import re
import time
import hashlib
from typing import List, Optional, Dict
from bs4 import BeautifulSoup
from . import BaseSpider, SearchResult


class LostFilmSpider(BaseSpider):
    """Spider for lostfilm.tv"""

    BASE_URL = "https://www.lostfilm.tv"
    USE_TOR = False

    def __init__(self, tor_proxy: Optional[str] = None):
        super().__init__(tor_proxy)

    def get_name(self) -> str:
        return "LostFilm"

    def search(self, query: str) -> List[SearchResult]:
        """Search for content on LostFilm"""
        results = []

        try:
            # Search query
            search_url = f"{self.BASE_URL}/search/?q={query}"
            
            print(f"[LostFilm] Searching: {search_url}")

            resp = self.get(search_url)
            html = resp.text

            soup = BeautifulSoup(html, "lxml")

            # Find search results - LostFilm uses different structure
            # Try multiple selectors
            search_results = []
            
            # Try 1: div.search-result
            search_results = soup.find_all("div", class_="search-result")
            
            # Try 2: div.search-item
            if not search_results:
                search_results = soup.find_all("div", class_="search-item")
            
            # Try 3: Any div with onclick containing PlayEpisode
            if not search_results:
                search_results = soup.find_all("div", onclick=re.compile(r"PlayEpisode"))
            
            # Try 4: Links to /series/ or /movie/
            if not search_results:
                links = soup.find_all("a", href=re.compile(r"/(series|movie)/"))
                search_results = [link.parent for link in links]

            if not search_results:
                # Debug: print available classes
                all_classes = set()
                for tag in soup.find_all(class_=True):
                    classes = tag.get('class', [])
                    all_classes.update(classes)
                print(f"[LostFilm] Available classes: {list(all_classes)[:20]}")
                print(f"[LostFilm] No results found for '{query}'")
                return results

            print(f"[LostFilm] Found {len(search_results)} search result elements")

            for result in search_results:
                try:
                    # Get title and link
                    title_link = result.find("a")
                    if not title_link:
                        title_link = result.find("div", class_=re.compile(r"title|name"))
                    
                    if not title_link:
                        continue

                    # Get Russian title
                    title_ru = title_link.get_text(strip=True)
                    href = title_link.get("href", "")
                    
                    if href and not href.startswith("http"):
                        href = f"{self.BASE_URL}{href}"

                    # Get type (movie/series)
                    content_type = "unknown"
                    type_tag = result.find("span", class_=re.compile(r"type|kind"))
                    if type_tag:
                        content_type = type_tag.get_text(strip=True)
                    elif "/series/" in href:
                        content_type = "Сериал"
                    elif "/movie/" in href:
                        content_type = "Фильм"

                    # Get year
                    year = ""
                    year_tag = result.find("span", class_=re.compile(r"year|date"))
                    if year_tag:
                        year = year_tag.get_text(strip=True)
                    else:
                        # Try to extract from title
                        year_match = re.search(r'\b(19|20)\d{2}\b', title_ru)
                        if year_match:
                            year = year_match.group()

                    # Get image
                    poster = ""
                    img_tag = result.find("img")
                    if img_tag:
                        poster = img_tag.get("src", "")
                        if poster and not poster.startswith("http"):
                            poster = f"{self.BASE_URL}{poster}"

                    # Get original title (English) from URL or fetch from page
                    title_en = title_ru  # Default to Russian
                    if href:
                        # Extract from URL: /series/Supernatural -> Supernatural
                        url_match = re.search(r'/(?:series|movie)/([^/]+)', href)
                        if url_match:
                            title_en = url_match.group(1).replace('-', ' ').title()
                    
                    # Always add result even if href is empty (will fetch on selection)
                    results.append(
                        SearchResult(
                            title=title_en or "Unknown",  # Use English title
                            magnet=href or "",  # Store URL temporarily (may be empty)
                            tracker="LostFilm",
                            size="",
                            seeds=0,
                            peers=0,
                            year=year,
                            quality="HD",
                            extra={
                                "type": content_type,
                                "url": href,
                                "poster": poster,
                                "title_ru": title_ru,  # Store Russian title for display
                            }
                        )
                    )

                except Exception as e:
                    print(f"[LostFilm] Error parsing search result: {e}")
                    import traceback
                    traceback.print_exc()
                    continue

            print(f"[LostFilm] Found {len(results)} results for '{query}'")

        except Exception as e:
            print(f"[LostFilm] Search error: {e}")
            import traceback
            traceback.print_exc()

        return results

    def get_movie_download(self, movie_url: str) -> Optional[str]:
        """Get magnet link for movie"""
        try:
            resp = self.get(movie_url)
            html = resp.text

            soup = BeautifulSoup(html, "lxml")

            # Find PlayEpisode button
            play_btn = soup.find("div", class_="external-btn")
            if not play_btn:
                print(f"[LostFilm] No download button found for {movie_url}")
                return None

            # Get episode ID from onclick
            onclick = play_btn.get("onclick", "")
            match = re.search(r"PlayEpisode\('(\d+)'\)", onclick)
            if not match:
                print(f"[LostFilm] No episode ID found in {onclick}")
                return None

            episode_id = match.group(1)
            print(f"[LostFilm] Found episode ID: {episode_id}")

            # Get download page
            download_url = f"{self.BASE_URL}/V/?c={episode_id}"
            resp = self.get(download_url)
            
            # Follow redirects
            if resp.status_code == 200 and 'tracktor.site' in resp.url:
                # Extract torrent link from redirect page
                soup = BeautifulSoup(resp.text, "lxml")
                
                # Find all quality options
                quality_links = soup.find_all("a", href=re.compile(r"tracktor\.site"))
                
                if not quality_links:
                    print(f"[LostFilm] No torrent links found")
                    return None

                # Prefer 1080p
                torrent_url = None
                for link in quality_links:
                    href = link.get("href", "")
                    text = link.get_text().lower()
                    
                    if "1080p" in text:
                        torrent_url = href
                        print(f"[LostFilm] Selected 1080p quality")
                        break
                    elif "720p" in text and not torrent_url:
                        torrent_url = href
                    elif not torrent_url:
                        torrent_url = href

                if torrent_url:
                    # Download torrent file and convert to magnet
                    return self.torrent_to_magnet(torrent_url)

            return None

        except Exception as e:
            print(f"[LostFilm] Error getting movie download: {e}")
            return None

    def torrent_to_magnet(self, torrent_url: str) -> Optional[str]:
        """Download torrent file and convert to magnet link"""
        try:
            # Download torrent file
            resp = self.get(torrent_url)
            
            if resp.status_code != 200:
                print(f"[LostFilm] Failed to download torrent: {resp.status_code}")
                return None

            torrent_data = resp.content

            # Parse torrent to get info hash
            import bencoder
            torrent = bencoder.decode(torrent_data)
            
            # Get info hash
            info_hash = hashlib.sha1(bencoder.encode(torrent[b'info'])).hexdigest()
            
            # Get name
            name = torrent[b'info'].get(b'name', b'Unknown').decode('utf-8', errors='ignore')
            
            # Get size
            size = sum(torrent[b'info'].get(b'length', 0) for torrent in torrent.get(b'files', []))
            if not size:
                size = torrent[b'info'].get(b'length', 0)

            # Create magnet link
            magnet = f"magnet:?xt=urn:btih:{info_hash}&dn={name}"
            
            # Add trackers
            trackers = torrent.get(b'announce-list', [])
            if trackers:
                for tracker_list in trackers:
                    for tracker in tracker_list:
                        magnet += f"&tr={tracker.decode('utf-8')}"
            
            print(f"[LostFilm] Created magnet for: {name}")
            return magnet

        except Exception as e:
            print(f"[LostFilm] Error converting torrent to magnet: {e}")
            return None

    def get_series_episodes(self, series_url: str) -> Optional[List[Dict]]:
        """Get episodes list for series (not implemented yet)"""
        # TODO: Implement series episodes parsing
        print(f"[LostFilm] Series parsing not implemented yet: {series_url}")
        return None
