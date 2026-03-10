"""
Rutor spider - Russian open torrent tracker
No login required
"""

import re
from typing import List, Optional, Dict
from bs4 import BeautifulSoup
from . import BaseSpider, SearchResult


class RutorSpider(BaseSpider):
    """Spider for rutor.info"""

    BASE_URL = "http://rutor.info"
    BASE_URL_TOR = "http://rutorc6mqdinc4cz.onion"
    USE_TOR = True  # Use Tor proxy

    # Forum categories
    FORUM_KEYS = [
        1,  # Зарубежные фильмы
        4,  # Зарубежные сериалы
        7,  # Мультипликация
        10,  # Аниме
    ]

    def __init__(self, tor_proxy: Optional[str] = None):
        super().__init__(tor_proxy)

    def get_name(self) -> str:
        return "Rutor"

    def search(self, query: str, max_pages: int = 5) -> List[SearchResult]:
        """Search torrents by query with pagination"""
        results = []

        try:
            # Search via search page - parse multiple pages
            page = 0
            while page < max_pages:
                search_url = "/search/{}/0/000/0/{}".format(page, query)

                resp = self.get(search_url)
                html = resp.text

                soup = BeautifulSoup(html, "lxml")

                # Find results table
                table = (
                    soup.find("div", {"id": "index"}).find("table")
                    if soup.find("div", {"id": "index"})
                    else None
                )
                if not table:
                    print(f"[Rutor] No results table found on page {page + 1}")
                    break

                # Parse each row (skip header)
                page_results = []
                for row in table.find_all("tr")[1:]:
                    try:
                        tds = row.find_all("td")
                        if len(tds) < 2:
                            continue

                        # Get magnet and title
                        magnet_link = row.find("a", href=re.compile(r"magnet:"))
                        if not magnet_link:
                            continue

                        magnet = magnet_link.get("href")

                        # Get title from second link (not magnet)
                        links = row.find_all("a")
                        title = ""
                        torrent_url = ""
                        for link in links:
                            href = link.get("href", "")
                            if href.startswith("/torrent/"):
                                title = link.get_text(strip=True)
                                torrent_url = href
                                break

                        if not title:
                            continue

                        # Get seeds/leech
                        seed_span = row.find("span", class_="green")
                        leech_span = row.find("span", class_="red")

                        seeds = self.clean_number(seed_span.get_text()) if seed_span else 0
                        leechers = (
                            self.clean_number(leech_span.get_text()) if leech_span else 0
                        )

                        # Get size
                        size = ""
                        # Try to extract size from HTML
                        size_match = re.search(r"(\d+\.?\d*)\s*(GB|MB|TB)", str(row))
                        if size_match:
                            size = f"{size_match.group(1)} {size_match.group(2)}"

                        # Extract year from title
                        year = self.extract_year(title)

                        # Detect quality
                        quality = self.detect_quality(title)

                        page_results.append(
                            SearchResult(
                                title=title,
                                magnet=magnet,
                                tracker="Rutor",
                                size=size,
                                seeds=seeds,
                                peers=seeds + leechers,
                                year=year,
                                quality=quality,
                            )
                        )

                    except Exception as e:
                        print(f"[Rutor] Error parsing row: {e}")
                        continue

                print(f"[Rutor] Found {len(page_results)} results on page {page + 1}")
                results.extend(page_results)

                # Check if there are more pages
                if len(page_results) < 25:  # Rutor shows ~25 results per page
                    print(f"[Rutor] Last page (only {len(page_results)} results)")
                    break

                # Check for next page link
                next_page_link = soup.find("a", string=str(page + 2))
                if not next_page_link:
                    print(f"[Rutor] No more pages found")
                    break

                page += 1

            print(f"[Rutor] Total results: {len(results)} for '{query}'")

        except Exception as e:
            print(f"[Rutor] Search error: {e}")

        return results

    def get_topic_details(self, torrent_url: str) -> Optional[Dict]:
        """Get detailed info about a torrent"""
        try:
            resp = self.get(torrent_url)
            html = resp.text

            soup = BeautifulSoup(html, "lxml")

            # Check if torrent exists
            if "Раздача не существует" in html:
                return None

            # Get title
            title_tag = soup.find("h1")
            if title_tag:
                title = title_tag.get_text(strip=True)
            else:
                title = "Unknown"

            # Find magnet link
            magnet = None
            download_div = soup.find("div", {"id": "download"})
            if download_div:
                magnet = self.extract_magnet(str(download_div))

            # Get seeds/leech from details table
            seeds = 0
            leechers = 0

            details_table = soup.find("div", {"id": "details"})
            if details_table:
                rows = details_table.find_all("tr")
                for row in rows:
                    text = row.get_text()
                    if "Раздают" in text:
                        td = row.find_all("td")
                        if len(td) > 1:
                            seeds = self.clean_number(td[-1].get_text())
                    if "Качают" in text:
                        td = row.find_all("td")
                        if len(td) > 1:
                            leechers = self.clean_number(td[-1].get_text())

            return {
                "title": title,
                "magnet": magnet,
                "seeds": seeds,
                "leechers": leechers,
            }

        except Exception as e:
            print(f"[Rutor] Error getting topic {torrent_url}: {e}")
            return None

    def search_by_category(self, category_id: int, page: int = 0) -> List[SearchResult]:
        """Search by category (browse mode)"""
        results = []

        try:
            url = "/browse/{}/{}/0/0".format(page, category_id)
            resp = self.get(url)
            html = resp.text

            soup = BeautifulSoup(html, "lxml")
            table = (
                soup.find("div", {"id": "index"}).find("table")
                if soup.find("div", {"id": "index"})
                else None
            )

            if not table:
                return results

            for row in table.find_all("tr")[1:]:
                try:
                    magnet_link = row.find("a", href=re.compile(r"magnet:"))
                    if not magnet_link:
                        continue

                    magnet = magnet_link.get("href")

                    # Get title
                    title = ""
                    for link in row.find_all("a"):
                        if link.get("href", "").startswith("/torrent/"):
                            title = link.get_text(strip=True)
                            break

                    if not title:
                        continue

                    # Get seeds/leech
                    seed_span = row.find("span", class_="green")
                    leech_span = row.find("span", class_="red")

                    seeds = self.clean_number(seed_span.get_text()) if seed_span else 0
                    leechers = (
                        self.clean_number(leech_span.get_text()) if leech_span else 0
                    )

                    # Extract year and quality
                    year = self.extract_year(title)
                    quality = self.detect_quality(title)

                    results.append(
                        SearchResult(
                            title=title,
                            magnet=magnet,
                            tracker="Rutor",
                            seeds=seeds,
                            peers=seeds + leechers,
                            year=year,
                            quality=quality,
                        )
                    )

                except Exception as e:
                    continue

        except Exception as e:
            print(f"[Rutor] Category search error: {e}")

        return results
