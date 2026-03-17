"""
Torrent manager - uses popcorn-mpv for streaming
"""

import os
import re
import subprocess
import json
import time
from typing import Dict, Any, Optional

from torrent_search import TorrentSearcher
from config import TORRENT_DOWNLOAD_DIR


class TorrentStatus:
    """Torrent status tracker"""

    def __init__(self):
        self.status = "idle"
        self.progress = 0
        self.speed = "0 MB/s"
        self.peers = 0
        self.file = ""
        self.time = "0:00"
        self.playback_position = 0  # Current playback position in seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "progress": self.progress,
            "speed": self.speed,
            "peers": self.peers,
            "file": self.file,
            "time": self.time,
            "playback_position": self.playback_position,
        }

    def update_from_log(self, log_path: str) -> None:
        """Update status from popcorn-mpv log file"""
        if not os.path.exists(log_path):
            return

        try:
            with open(log_path, "r") as f:
                content = f.read()
                lines = content.split('\n')
                
                if not lines:
                    return

                # Get last 50 lines
                for line in reversed(lines[-50:]):
                    line = line.strip()

                    # Parse progress percentage
                    if "%" in line and "Прогресс" in line:
                        match = re.search(r"Прогресс:\s*(\d+\.?\d*)%", line)
                        if match:
                            self.progress = float(match.group(1))

                    # Parse speed
                    match = re.search(r"((\d+\.?\d*)\s*(MB|KB|GB)/s)", line)
                    if match:
                        self.speed = match.group(1)

                    # Parse peers
                    match = re.search(r"Пиров:\s*(\d+)", line)
                    if match:
                        self.peers = int(match.group(1))

                    # Check if streaming
                    if "Запуск MPV" in line or "MPV запущен" in line:
                        self.status = "playing"
                    
                    # Check if completed
                    if "100%" in line or "завершено" in line.lower():
                        self.status = "completed"
        except Exception as e:
            print(f"[Status] Error reading log: {e}")
            pass

    def check_process_running(self) -> None:
        """Check if popcorn-mpv process is still running"""
        try:
            # Check for node server.js process (popcorn-mpv)
            result = subprocess.run(
                ["pgrep", "-f", "node.*server.js"], capture_output=True, text=True
            )
            node_running = result.returncode == 0
            
            # Check for mpv process
            mpv_result = subprocess.run(
                ["pgrep", "-f", "mpv"], capture_output=True, text=True
            )
            mpv_running = mpv_result.returncode == 0
            
            # Consider running if either node or mpv is running
            if not (node_running or mpv_running):
                if self.status not in ["stopped", "completed"]:
                    self.status = "stopped"
        except:
            pass


class TorrentManager:
    """Manage torrent search and streaming using popcorn-mpv"""

    SELECTED_TORRENTS_FILE = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "selected_torrents.json"
    )
    TORRENT_HISTORY_FILE = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "torrent_history.json"
    )
    PLAYBACK_PROGRESS_FILE = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "playback_progress.json"
    )
    CACHE_DURATION = 7200  # 2 hours cache (increased from 1 hour)
    MAX_CACHE_SIZE = 1000  # Maximum number of queries to cache
    DOWNLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")
    SERVER_JS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "server.js")
    LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    LOG_PATH = os.path.join(LOG_DIR, "striming-torrent-mpv.log")

    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.searcher = TorrentSearcher()
        self.status = TorrentStatus()
        self.current_process = None
        os.makedirs(os.path.join(self.project_dir, "data"), exist_ok=True)
        os.makedirs(self.DOWNLOADS_DIR, exist_ok=True)
        os.makedirs(self.LOG_DIR, exist_ok=True)

    def search(self, query: str, use_cache: bool = True) -> list[Dict[str, Any]]:
        """Search for torrents with caching"""
        if not query:
            return []

        cache_key = query.lower().strip()

        # Try to get from cache
        if use_cache:
            cache = self._load_torrent_cache()
            if cache_key in cache and self._is_cache_valid(cache[cache_key]):
                print(f"[Cache] Hit for query: {query}")
                results = cache[cache_key].get("results", [])
                return self._prioritize_selected(results, query)
            elif cache_key in cache:
                print(f"[Cache] Expired for query: {query}")

        # Search from scratch
        print(f"[Search] Searching for: {query}")
        results = self.searcher.search_all(query)
        
        # Convert TorrentResult objects to dictionaries
        results_dict = []
        for r in results:
            if hasattr(r, 'to_dict'):
                results_dict.append(r.to_dict())
            else:
                results_dict.append(r)
        results = results_dict

        if not results:
            print(f"[Search] No results from trackers for: {query}")
            results = [
                {
                    "title": f"No torrents found for '{query}'",
                    "year": "",
                    "quality": "N/A",
                    "size": "Try another search",
                    "seeds": 0,
                    "peers": 0,
                    "magnet": "",
                    "tracker": "None",
                    "type": "error",
                }
            ]

        # Save to cache
        if use_cache and results:
            cache = self._load_torrent_cache()
            cache[cache_key] = {
                "query": query,
                "results": results,
                "timestamp": time.time(),
                "count": len(results),
            }
            self._save_torrent_cache(cache)
            print(f"[Cache] Saved {len(results)} results for: {query}")

        return self._prioritize_selected(results, query)

    def _get_torrent_id(self, magnet: str) -> str:
        """Generate unique ID from magnet link"""
        if not magnet:
            return ""
        match = re.search(r"btih:([a-fA-F0-9]{40})", magnet)
        if match:
            return match.group(1).lower()
        return ""

    def _load_selected_torrents(self) -> Dict:
        """Load last selected torrent from file"""
        if os.path.exists(self.SELECTED_TORRENTS_FILE):
            try:
                with open(self.SELECTED_TORRENTS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_selected_torrent(self, magnet: str, title: str, query: str):
        """Save only the last selected torrent"""
        try:
            selected = {
                "magnet": magnet,
                "title": title,
                "query": query,
                "timestamp": time.time(),
            }

            with open(self.SELECTED_TORRENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(selected, f, ensure_ascii=False, indent=2)
            print(f"[TorrentManager] Saved last selected torrent: {title[:50]}...")
        except Exception as e:
            print(f"Error saving selected torrent: {e}")

    def _prioritize_selected(self, results: list, query: str) -> list:
        """Prioritize only the last selected torrent"""
        selected = self._load_selected_torrents()

        if not selected:
            for result in results:
                result["selected"] = False
                result["selected_at"] = 0
            return results

        selected_magnet = selected.get("magnet", "")
        selected_id = self._get_torrent_id(selected_magnet)

        for result in results:
            magnet = result.get("magnet", "")
            torrent_id = self._get_torrent_id(magnet)

            if torrent_id and torrent_id == selected_id:
                result["selected"] = True
                result["selected_at"] = selected.get("timestamp", 0)
            else:
                result["selected"] = False
                result["selected_at"] = 0

        results.sort(key=lambda x: (not x.get("selected", False), -x.get("seeds", 0)))
        return results

    def _load_torrent_cache(self) -> Dict:
        """Load torrent cache from file"""
        cache_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "torrent_cache.json"
        )
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_torrent_cache(self, cache: Dict):
        """Save torrent cache to file with size limit"""
        cache_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "torrent_cache.json"
        )
        try:
            # Clean old entries if cache is too large
            if len(cache) > self.MAX_CACHE_SIZE:
                # Sort by timestamp and keep only newest entries
                sorted_cache = sorted(
                    cache.items(),
                    key=lambda x: x[1].get("timestamp", 0),
                    reverse=True
                )[:self.MAX_CACHE_SIZE]
                cache = dict(sorted_cache)
                print(f"[Cache] Cleaned to {self.MAX_CACHE_SIZE} entries")
            
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}")

    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid (2 hours)"""
        if not cache_entry:
            return False
        timestamp = cache_entry.get("timestamp", 0)
        return (time.time() - timestamp) < self.CACHE_DURATION  # 2 hours

    def clear_cache(self):
        """Clear torrent cache"""
        try:
            cache_file = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "data", "torrent_cache.json"
            )
            if os.path.exists(cache_file):
                os.remove(cache_file)
                print("[Cache] Cleared")
        except Exception as e:
            print(f"Error clearing cache: {e}")

    # ==================== Series Support ====================

    def get_episode_file(self, magnet: str, season: int, episode: int) -> Optional[str]:
        """Get episode file path from torrent by SXXEYY pattern"""
        try:
            # For now, return a pattern that will be matched during streaming
            # Format: S02E01 or S10E01 (with leading zero for season < 10)
            if season < 10:
                pattern = f"S{season:02d}E{episode:02d}"
            else:
                pattern = f"S{season}E{episode:02d}"
            
            print(f"[Series] Looking for file pattern: {pattern}")
            return pattern
        except Exception as e:
            print(f"[Series] Error getting episode file: {e}")
            return None

    def search_series(self, series_name: str, season: int) -> list:
        """Search for series with specific season"""
        try:
            from torrent_search import TorrentSearcher
            searcher = TorrentSearcher()
            return searcher.search_series(series_name, season)
        except Exception as e:
            print(f"[Series] Search error: {e}")
            return []

    # ==================== Playback Progress ====================

    def save_playback_progress(self, magnet: str, position: int, duration: int):
        """Save playback position for a torrent"""
        try:
            progress = self._load_playback_progress()
            torrent_id = self._get_torrent_id(magnet)
            
            if torrent_id:
                progress[torrent_id] = {
                    "position": position,
                    "duration": duration,
                    "timestamp": time.time(),
                    "formatted": self._format_time(position),
                    "formatted_position": self._format_time(position),
                }
                
                with open(self.PLAYBACK_PROGRESS_FILE, "w", encoding="utf-8") as f:
                    json.dump(progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving playback progress: {e}")

    def get_playback_progress(self, magnet: str) -> Dict[str, Any]:
        """Get playback progress for a torrent"""
        progress = self._load_playback_progress()
        torrent_id = self._get_torrent_id(magnet)
        
        if torrent_id and torrent_id in progress:
            return progress[torrent_id]
        return {"position": 0, "duration": 0, "formatted": "0:00"}

    def _load_playback_progress(self) -> Dict:
        """Load playback progress from file"""
        if os.path.exists(self.PLAYBACK_PROGRESS_FILE):
            try:
                with open(self.PLAYBACK_PROGRESS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _format_time(self, seconds: int) -> str:
        """Format seconds to HH:MM (no seconds)"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours > 0:
            return f"{hours}:{minutes:02d}"
        return f"{minutes}"

    # ==================== History ====================

    def _load_torrent_history(self) -> list:
        """Load torrent history from file"""
        if os.path.exists(self.TORRENT_HISTORY_FILE):
            try:
                with open(self.TORRENT_HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return []

    def _save_torrent_history(self, magnet: str, title: str, query: str):
        """Save to torrent history - only movie title"""
        try:
            history = self._load_torrent_history()
            clean_title = self._extract_movie_title(title, query)

            for item in history:
                if item.get("title") == clean_title:
                    history.remove(item)
                    break

            history.insert(0, {
                "title": clean_title,
                "query": query,
                "timestamp": time.time(),
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            })

            history = history[:50]

            with open(self.TORRENT_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            print(f"[TorrentManager] Saved to history: {clean_title}")
        except Exception as e:
            print(f"Error saving to history: {e}")

    def get_torrent_history(self) -> list:
        """Get torrent history"""
        return self._load_torrent_history()

    def _extract_movie_title(self, full_title: str, query: str) -> str:
        """Extract clean movie title from full torrent title"""
        if query:
            return query.strip()
        
        clean = full_title
        import re
        clean = re.sub(r'\b(1080p|720p|2160p|4K|BluRay|WEB-DL|HDRip|DVDRip)\b', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'[\[\(]\d{4}[\]\)]', '', clean)
        clean = re.sub(r'\b\d{3,4}p\b', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\b(x264|x265|h264|h265|HEVC|AVC)\b', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\b(AAC|AC3|DTS|FLAC|MP3)\b', '', clean, flags=re.IGNORECASE)
        clean = re.sub(r'\b(YTS|YIFY|RARBG|EVO|FGT|Galaxy)\b', '', clean, flags=re.IGNORECASE)
        clean = clean.strip(' .-_')
        clean = ' '.join(clean.split())
        
        return clean if clean else full_title

    # ==================== Streaming with popcorn-mpv ====================

    def start_streaming(self, magnet: Optional[str] = None, title: str = "", query: str = "", episode_pattern: str = "") -> tuple[bool, str, str, Dict]:
        """Start torrent streaming with popcorn-mpv"""
        print("=" * 60)
        print("[POPCORN-MPV] Received start request")
        print("=" * 60)

        if not magnet:
            magnet = "magnet:?xt=urn:btih:08ada5a7a6183aae1e09d831df6748d566095a10&dn=Sintel"

        print(f"[POPCORN-MPV] Magnet link: {magnet[:50]}...")
        print(f"[POPCORN-MPV] Title: {title}")
        print(f"[POPCORN-MPV] Query: {query}")
        print(f"[POPCORN-MPV] Episode Pattern: {episode_pattern}")
        print("=" * 60)

        try:
            # Clear old log file before starting new session
            if os.path.exists(self.LOG_PATH):
                os.remove(self.LOG_PATH)
                print(f"[POPCORN-MPV] Cleared old log file")
            
            # Save to history
            if title and query:
                self._save_selected_torrent(magnet, title, query)
                self._save_torrent_history(magnet, title, query)

            # Kill old processes
            os.system("pkill -9 -f 'node server.js' 2>/dev/null || true")
            os.system("pkill -9 mpv 2>/dev/null || true")
            time.sleep(2)

            # Start striming-torrent-mpv server with episode pattern
            if episode_pattern:
                cmd = f'cd {self.project_dir} && nohup node server.js "{magnet}" --episode "{episode_pattern}" > {self.LOG_PATH} 2>&1 &'
            else:
                cmd = f'cd {self.project_dir} && nohup node server.js "{magnet}" > {self.LOG_PATH} 2>&1 &'
            
            print(f"[POPCORN-MPV] Starting: {cmd}")
            print(f"[POPCORN-MPV] Log file: {self.LOG_PATH}")
            os.system(cmd)

            # Wait for server to start with faster polling (500ms)
            print("[POPCORN-MPV] Waiting for server to start (15s)...")

            for i in range(30):  # 30 * 500ms = 15 seconds
                time.sleep(0.5)  # Check every 500ms
                # Check if process started
                result = subprocess.run(['pgrep', '-f', 'node.*server.js'], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"[POPCORN-MPV] Process started after {(i+1)*0.5} seconds")
                    # Also check if port 8888 is listening
                    try:
                        import socket
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock_result = sock.connect_ex(('localhost', 8888))
                        sock.close()
                        if sock_result == 0:
                            print("[POPCORN-MPV] Port 8888 is listening")

                            # Read file index from log
                            file_index = 0  # Default
                            try:
                                with open(self.LOG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                                    for line in f:
                                        if 'Индекс файла:' in line:
                                            match = re.search(r'Индекс файла:\s*(\d+)', line)
                                            if match:
                                                file_index = int(match.group(1))
                                                print(f"[POPCORN-MPV] File index: {file_index}")
                                            break
                            except Exception as e:
                                print(f"[POPCORN-MPV] Error reading file index: {e}")

                            self.status.status = "playing"
                            progress = self.get_playback_progress(magnet)
                            return True, "Popcorn-MPV started", f"http://localhost:8888/{file_index}", progress
                    except:
                        pass
                    # Process exists but port not ready yet, continue waiting

            # Timeout - check if process exists anyway
            result = subprocess.run(['pgrep', '-f', 'node.*server.js'], capture_output=True, text=True)
            if result.returncode == 0:
                print("[POPCORN-MPV] Process exists, assuming it's working")

                # Read file index from log
                file_index = 0
                try:
                    with open(self.LOG_PATH, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            if 'Индекс файла:' in line:
                                match = re.search(r'Индекс файла:\s*(\d+)', line)
                                if match:
                                    file_index = int(match.group(1))
                                break
                except Exception as e:
                    print(f"[POPCORN-MPV] Error reading file index: {e}")

                self.status.status = "playing"
                progress = self.get_playback_progress(magnet)
                return True, "Popcorn-MPV started (slow)", f"http://localhost:8888/{file_index}", progress

            print("[POPCORN-MPV] Failed to start process")
            return False, "Failed to start popcorn-mpv", "", {}

        except Exception as e:
            print(f"[POPCORN-MPV] Exception: {e}")
            return False, str(e), "", {}

    def stop_streaming(self) -> bool:
        """Stop torrent streaming"""
        try:
            os.system("pkill -f 'popcorn-mpv' 2>/dev/null || true")
            os.system("pkill -f 'node.*server.js' 2>/dev/null || true")
            self.status.status = "stopped"
            print("[POPCORN-MPV] Stopped")
            return True
        except Exception as e:
            print(f"Error stopping torrent: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get current torrent streaming status"""
        self.status.update_from_log(self.LOG_PATH)
        status = self.status.to_dict()

        # Try to get additional info from log
        if os.path.exists(self.LOG_PATH):
            try:
                with open(self.LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
                    log_content = f.read()

                    # Parse filename
                    filename_match = re.search(r'Playing:\s*(.+?)(?:\n|$)', log_content)
                    if filename_match:
                        status["filename"] = filename_match.group(1).strip()

                    # Parse download speed
                    speed_match = re.search(r'Download speed:\s*([\d.]+\s*[MGK]B/s)', log_content)
                    if speed_match:
                        status["download_speed"] = speed_match.group(1)

                    # Parse peers/seeds
                    peers_match = re.search(r'Peers:\s*(\d+)', log_content)
                    if peers_match:
                        status["peers"] = int(peers_match.group(1))

                    seeds_match = re.search(r'Seeds:\s*(\d+)', log_content)
                    if seeds_match:
                        status["seeds"] = int(seeds_match.group(1))

                    # Parse downloaded/uploaded
                    downloaded_match = re.search(r'Downloaded:\s*([\d.]+\s*[MGK]B)', log_content)
                    if downloaded_match:
                        status["downloaded"] = downloaded_match.group(1)

                    uploaded_match = re.search(r'Uploaded:\s*([\d.]+\s*[MGK]B)', log_content)
                    if uploaded_match:
                        status["uploaded"] = uploaded_match.group(1)

                    # Parse time
                    time_match = re.search(r'Time:\s*(\d+:\d+)', log_content)
                    if time_match:
                        status["time"] = time_match.group(1)

                    # Parse progress
                    progress_match = re.search(r'Progress:\s*([\d.]+)%', log_content)
                    if progress_match:
                        status["progress"] = float(progress_match.group(1))

                    # Parse torrent progress from server.js output
                    # Format: 📊 Прогресс: 4.5% | ⬇ 880.0 MB | 📶 Пиров: 18 | ⚡ 1.08 MB/s
                    # Find LAST occurrence (most recent)
                    torrent_progress_matches = list(re.finditer(r'📊 Прогресс:\s*([\d.]+)%\s*\|\s*⬇\s*([\d.]+)\s*MB\s*\|\s*📶 Пиров:\s*(\d+)\s*\|\s*⚡\s*([\d.]+)\s*MB/s', log_content))
                    if torrent_progress_matches:
                        last_match = torrent_progress_matches[-1]  # Get last (most recent) match
                        status["progress"] = float(last_match.group(1))
                        status["downloaded"] = f"{last_match.group(2)} MB"
                        status["peers"] = int(last_match.group(3))
                        status["download_speed"] = f"{last_match.group(4)} MB/s"

                    # Parse MPV AV line - find LAST occurrence (most recent)
                    # Format: AV: 00:00:57 / 00:23:15 (4%) A-V:  0.000 Cache: 30s/30MB
                    av_matches = list(re.finditer(r'AV:\s*(\d+:\d+:\d+)\s*/\s*(\d+:\d+:\d+)\s*\((\d+)%\)', log_content))
                    if av_matches:
                        last_av = av_matches[-1]  # Get last (most recent) match
                        status["av_current"] = last_av.group(1)
                        status["av_total"] = last_av.group(2)
                        status["av_percent"] = int(last_av.group(3))
                        status["av_line"] = f"AV: {last_av.group(1)} / {last_av.group(2)} ({last_av.group(3)}%)"

            except Exception as e:
                print(f"[STATUS] Error reading log from {self.LOG_PATH}: {e}")

        # Check if MPV exited (look for exit message in log AFTER last AV line)
        # This prevents false positives from previous sessions
        mpv_exited = False
        if os.path.exists(self.LOG_PATH):
            try:
                with open(self.LOG_PATH, "r", encoding="utf-8", errors="ignore") as f:
                    log_content = f.read()
                    
                    # Find position of last AV line
                    av_matches = list(re.finditer(r'AV:\s*(\d+:\d+:\d+)\s*/\s*(\d+:\d+:\d+)\s*\((\d+)%\)', log_content))
                    if av_matches:
                        last_av_pos = av_matches[-1].end()
                        # Check if there's an exit message AFTER the last AV line
                        content_after_av = log_content[last_av_pos:]
                        if "Exiting... (Quit)" in content_after_av or "MPV закрыт" in content_after_av:
                            mpv_exited = True
            except:
                pass

        # Check if processes are running
        try:
            result = subprocess.run(["pgrep", "-f", "node.*server.js"], capture_output=True, text=True)
            node_running = result.returncode == 0
            mpv_result = subprocess.run(["pgrep", "-f", "mpv"], capture_output=True, text=True)
            mpv_running = mpv_result.returncode == 0

            processes_running = node_running or mpv_running
        except:
            processes_running = False

        # Determine final status
        if mpv_exited:
            # MPV explicitly exited
            status["status"] = "stopped"
            status["playing"] = False
        elif processes_running:
            # Processes are running, consider it playing (even if no data yet)
            status["status"] = "playing"
            status["playing"] = True
        elif status.get("av_line") or status.get("download_speed"):
            # Processes not found but we have recent data
            status["status"] = "playing"
            status["playing"] = True
        else:
            # No processes, no data
            status["status"] = "stopped"
            status["playing"] = False

        return status
