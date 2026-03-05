"""
Kinozal spider - Russian torrent tracker (kinozal.ws)
"""

import re
from typing import List, Optional, Dict
from bs4 import BeautifulSoup
from urllib.parse import quote, urljoin
from . import BaseSpider, SearchResult
import time


class KinozalSpider(BaseSpider):
    """Spider for kinozal.ws"""

    BASE_URL = "https://kinozal.ws"
    BASE_URL_TOR = "http://kinozal4igins4ad7.onion"  # Tor mirror if available
    USE_TOR = False

    def __init__(self, tor_proxy: Optional[str] = None):
        super().__init__(tor_proxy)
        # Update headers for kinozal
        self.session.headers.update(
            {
                "Referer": "https://kinozal.ws/",
            }
        )

    def get_name(self) -> str:
        return "Kinozal"

    def _parse_movie_article_basic(self, article) -> Optional[Dict]:
        """Parse basic movie info from search results"""
        try:
            # Get title
            title_span = article.find("span", itemprop="name")
            if not title_span:
                return None

            # Extract title (remove <em> tags used for highlighting)
            title = title_span.get_text(strip=True)

            # Get movie URL
            title_link = article.find("a", class_="title")
            if not title_link:
                return None

            movie_path = title_link.get("href", "")
            if not movie_path:
                return None

            movie_url = urljoin(self.BASE_URL, str(movie_path))

            # Get year
            year_div = article.find("div", class_="fs-08")
            year = ""
            if year_div:
                year_match = re.search(r"\b(19|20)\d{2}\b", year_div.get_text())
                if year_match:
                    year = year_match.group(0)

            # Get alternative title (English name)
            alt_title_span = article.find("span", itemprop="alternativeHeadline")
            alt_title = ""
            if alt_title_span:
                alt_title = alt_title_span.get_text(strip=True)

            # Detect quality from title
            quality = self.detect_quality(title)

            # Build full title
            full_title = title
            if alt_title and alt_title != title:
                full_title = f"{title} / {alt_title}"
            if year:
                full_title += f" ({year})"

            return {
                "title": full_title,
                "url": movie_url,
                "year": year,
                "quality": quality,
            }

        except Exception as e:
            print(f"[Kinozal] Error parsing article: {e}")
            return None

    def search(self, query: str) -> List[SearchResult]:
        """Search torrents by query"""
        results = []

        try:
            print(f"[Kinozal] Starting search for: '{query}'")

            # Search URL
            encoded_query = quote(query)
            search_url = f"/search?q={encoded_query}&type=words&order_by=fsort"

            print(f"[Kinozal] Fetching: {search_url}")
            resp = self.get(search_url)
            html = resp.text

            print(f"[Kinozal] Response status: {resp.status_code}")
            print(f"[Kinozal] Response length: {len(html)} chars")

            if resp.status_code != 200:
                print(f"[Kinozal] Error: HTTP {resp.status_code}")
                return results

            soup = BeautifulSoup(html, "lxml")

            # Find all movie articles
            articles = soup.find_all("article", class_="movie")
            print(f"[Kinozal] Found {len(articles)} movie articles")

            if not articles:
                print("[Kinozal] No results found")
                return results

            # Parse each movie - first get basic info
            movies = []
            for article in articles[:15]:  # Limit to top 15
                try:
                    movie_info = self._parse_movie_article_basic(article)
                    if movie_info:
                        movies.append(movie_info)
                except Exception as e:
                    print(f"[Kinozal] Error parsing article: {e}")
                    continue

            print(f"[Kinozal] Found {len(movies)} movies, fetching download links...")

            # Note: Kinozal uses JavaScript to generate download links dynamically
            # We return results with the movie URL so users can visit the site to download
            for movie_info in movies:
                results.append(
                    SearchResult(
                        title=movie_info["title"],
                        magnet=movie_info[
                            "url"
                        ],  # Use URL as magnet (user can visit to download)
                        tracker="Kinozal",
                        year=movie_info.get("year", ""),
                        quality=movie_info.get("quality", "Unknown"),
                    )
                )

            print(f"[Kinozal] Successfully parsed {len(results)} results")

        except Exception as e:
            print(f"[Kinozal] Search error: {e}")
            import traceback

            traceback.print_exc()

        return results

    def get_magnet_from_page(self, movie_url: str) -> Optional[str]:
        """Get magnet link from movie detail page"""
        try:
            print(f"[Kinozal] Fetching magnet from: {movie_url}")
            resp = self.get(movie_url)

            if resp.status_code != 200:
                print(f"[Kinozal] Error: HTTP {resp.status_code}")
                return None

            # Look for magnet link directly
            magnet_match = re.search(r'href="(magnet:[^"]+)"', resp.text)
            if magnet_match:
                magnet = magnet_match.group(1)
                print(f"[Kinozal] Found magnet link")
                return magnet

            # Look for .torrent link
            torrent_match = re.search(r'href="(/download\.php\?[^"]+)"', resp.text)
            if torrent_match:
                torrent_url = torrent_match.group(1)
                full_url = urljoin(self.BASE_URL, torrent_url)
                print(f"[Kinozal] Found torrent link: {full_url}")
                # Return torrent URL as magnet alternative
                return full_url

            # Look for download button with data-id
            soup = BeautifulSoup(resp.text, "lxml")
            download_btn = soup.find("a", class_="dlt")
            if download_btn:
                dl_id = download_btn.get("data-id")
                if dl_id:
                    # Try to get download via API or alternate method
                    download_url = f"{self.BASE_URL}/download.php?id={dl_id}"
                    print(f"[Kinozal] Using download URL: {download_url}")
                    return download_url

            print("[Kinozal] No magnet or download link found")
            return None

        except Exception as e:
            print(f"[Kinozal] Error getting magnet: {e}")
            return None
