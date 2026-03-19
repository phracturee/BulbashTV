"""
Data managers for persistent storage (favorites, history)
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from models import FavoriteFolder, SearchHistoryItem, WatchHistoryItem


class DataManager:
    """Base class for data management"""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def _load_json(self, filename: str, default: Any) -> Any:
        """Load JSON file with error handling"""
        filepath = os.path.join(self.data_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading {filename}: {e}")
        return default

    def _save_json(self, filename: str, data: Any) -> None:
        """Save JSON file with error handling"""
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving {filename}: {e}")


class FavoritesManager(DataManager):
    """Manage favorite folders and items"""

    FAVORITES_FILE = "favorites.json"

    def __init__(self, data_dir: str):
        super().__init__(data_dir)
        self._favorites: Dict[str, FavoriteFolder] = {}
        self.load()

    def load(self) -> None:
        """Load favorites from file"""
        data = self._load_json(self.FAVORITES_FILE, {})
        if not data:
            # Create default folders
            data = {
                "default": {"name": "Избранное", "items": []},
                "watched": {"name": "Просмотренное", "items": []}
            }
        
        # Ensure watched folder exists
        if "watched" not in data:
            data["watched"] = {"name": "Просмотренное", "items": []}
        
        self._favorites = {
            k: FavoriteFolder.from_dict(v) for k, v in data.items()
        }

    def save(self) -> None:
        """Save favorites to file"""
        data = {k: v.to_dict() for k, v in self._favorites.items()}
        self._save_json(self.FAVORITES_FILE, data)

    @property
    def folders(self) -> Dict[str, FavoriteFolder]:
        """Get all folders"""
        return self._favorites

    def get_folder(self, folder_id: str) -> Optional[FavoriteFolder]:
        """Get folder by ID"""
        return self._favorites.get(folder_id)

    def create_folder(self, name: str) -> str:
        """Create new folder, returns folder ID"""
        import uuid

        folder_id = str(uuid.uuid4())[:8]
        self._favorites[folder_id] = FavoriteFolder(id=folder_id, name=name)
        self.save()
        return folder_id

    def delete_folder(self, folder_id: str) -> bool:
        """Delete folder (except default and watched)"""
        if folder_id in ["default", "watched"]:
            return False  # Cannot delete default folders
        if folder_id in self._favorites:
            del self._favorites[folder_id]
            self.save()
            return True
        return False

    def rename_folder(self, folder_id: str, name: str) -> bool:
        """Rename folder (except default and watched)"""
        if folder_id in ["default", "watched"]:
            return False  # Cannot rename default folders
        if folder_id in self._favorites:
            self._favorites[folder_id].name = name
            self.save()
            return True
        return False

    def add_item(
        self, folder_id: str, item: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """Add item to folder. Returns (success, message)"""
        if folder_id not in self._favorites:
            return False, "Folder not found"

        folder = self._favorites[folder_id]

        # Check if item already exists
        if any(i["id"] == item["id"] for i in folder.items):
            return False, "Already in this folder"

        # Add timestamp for sorting (newest first)
        item_with_timestamp = {
            **item,
            'timestamp': time.time()
        }

        folder.items.append(item_with_timestamp)
        self.save()
        return True, None

    def remove_item(self, item_id: int, folder_id: Optional[str] = None) -> None:
        """Remove item from folder(s)"""
        if folder_id and folder_id in self._favorites:
            # Remove from specific folder
            folder = self._favorites[folder_id]
            folder.items = [i for i in folder.items if i["id"] != item_id]
        else:
            # Remove from all folders
            for folder in self._favorites.values():
                folder.items = [i for i in folder.items if i["id"] != item_id]
        self.save()

    def is_favorite(self, item_id: int) -> bool:
        """Check if item is in any folder (except watched)"""
        for folder_id, folder in self._favorites.items():
            # Skip watched folder - it's not a favorite
            if folder_id == "watched":
                continue
            if any(item["id"] == item_id for item in folder.items):
                return True
        return False

    def is_watched(self, item_id: int) -> bool:
        """Check if item is in watched folder"""
        watched_folder = self._favorites.get("watched")
        if watched_folder:
            return any(item["id"] == item_id for item in watched_folder.items)
        return False

    def get_favorite_folders(self, item_id: int) -> List[str]:
        """Get list of folder IDs containing this item"""
        folders = []
        for folder_id, folder in self._favorites.items():
            if any(item["id"] == item_id for item in folder.items):
                folders.append(folder_id)
        return folders

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Convert to dictionary for templates"""
        return {k: v.to_dict() for k, v in self._favorites.items()}


class HistoryManager(DataManager):
    """Manage search and watch history"""

    SEARCH_HISTORY_FILE = "search_history.json"
    WATCH_HISTORY_FILE = "watch_history.json"

    def __init__(self, data_dir: str):
        super().__init__(data_dir)
        self._search_history: List[SearchHistoryItem] = []
        self._watch_history: List[WatchHistoryItem] = []
        self.load()

    def load(self) -> None:
        """Load history from files"""
        search_data = self._load_json(self.SEARCH_HISTORY_FILE, [])
        watch_data = self._load_json(self.WATCH_HISTORY_FILE, [])

        self._search_history = [
            SearchHistoryItem(**item) if isinstance(item, dict) else item
            for item in search_data
        ]
        self._watch_history = [
            WatchHistoryItem(**item) if isinstance(item, dict) else item
            for item in watch_data
        ]

    def save(self) -> None:
        """Save history to files"""
        self._save_json(
            self.SEARCH_HISTORY_FILE, [h.to_dict() for h in self._search_history]
        )
        self._save_json(
            self.WATCH_HISTORY_FILE, [h.to_dict() for h in self._watch_history]
        )

    # Search History
    def add_search_query(self, query: str) -> None:
        """Add search query to history"""
        if query and query not in [h.query for h in self._search_history]:
            self._search_history.insert(0, SearchHistoryItem(query=query))
            if len(self._search_history) > 20:
                self._search_history.pop()
            self.save()

    def remove_search_query(self, query: str) -> None:
        """Remove search query from history"""
        self._search_history = [h for h in self._search_history if h.query != query]
        self.save()

    def clear_search_history(self) -> None:
        """Clear search history"""
        self._search_history = []
        self.save()

    @property
    def search_history(self) -> List[SearchHistoryItem]:
        """Get search history"""
        return self._search_history

    def search_history_to_dict(self) -> List[Dict[str, Any]]:
        """Convert search history to dictionary"""
        return [h.to_dict() for h in self._search_history]

    # Watch History
    def add_watch(self, item: Dict[str, Any]) -> None:
        """Add item to watch history"""
        if item and item.get("id"):
            self._watch_history.insert(
                0,
                WatchHistoryItem(
                    id=item["id"],
                    title=item.get("title", ""),
                    media_type=item.get("media_type", ""),
                    poster_path=item.get("poster_path"),
                ),
            )
            if len(self._watch_history) > 100:
                self._watch_history.pop()
            self.save()

    def remove_watch(self, item_id: int) -> None:
        """Remove item from watch history"""
        self._watch_history = [h for h in self._watch_history if h.id != item_id]
        self.save()

    @property
    def watch_history(self) -> List[WatchHistoryItem]:
        """Get watch history"""
        return self._watch_history

    def watch_history_to_dict(self) -> List[Dict[str, Any]]:
        """Convert watch history to dictionary"""
        return [h.to_dict() for h in self._watch_history]
