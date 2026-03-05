"""
Data models for BulbashTV
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class MediaItem:
    """Base class for media items (movies and TV shows)"""

    id: int
    title: str
    overview: str
    poster_path: Optional[str]
    backdrop_path: Optional[str]
    release_date: str
    vote_average: float
    genre_ids: List[int]
    media_type: str  # "Фильм" or "Сериал"
    original_media_type: str  # "movie" or "tv"
    url: str
    is_favorite: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "title": self.title,
            "overview": self.overview,
            "poster_path": self.poster_path,
            "backdrop_path": self.backdrop_path,
            "release_date": self.release_date,
            "vote_average": self.vote_average,
            "genre_ids": self.genre_ids,
            "media_type": self.media_type,
            "original_media_type": self.original_media_type,
            "url": self.url,
            "is_favorite": self.is_favorite,
        }


@dataclass
class Movie(MediaItem):
    """Movie-specific data"""

    runtime: Optional[int] = None
    tagline: str = ""
    genres: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if self.media_type == "":
            self.media_type = "Фильм"
        if self.original_media_type == "":
            self.original_media_type = "movie"


@dataclass
class TVShow(MediaItem):
    """TV Show-specific data"""

    number_of_seasons: Optional[int] = None
    number_of_episodes: Optional[int] = None
    tagline: str = ""
    genres: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        if self.media_type == "":
            self.media_type = "Сериал"
        if self.original_media_type == "":
            self.original_media_type = "tv"


@dataclass
class FavoriteFolder:
    """Favorite folder with media items"""

    id: str
    name: str
    items: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name, "items": self.items}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FavoriteFolder":
        return cls(
            id=data.get("id", "default"),
            name=data.get("name", "Избранное"),
            items=data.get("items", []),
        )


@dataclass
class SearchHistoryItem:
    """Search history entry"""

    query: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {"query": self.query, "timestamp": self.timestamp}


@dataclass
class WatchHistoryItem:
    """Watch history entry"""

    id: int
    title: str
    media_type: str
    poster_path: Optional[str] = None
    watched_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "media_type": self.media_type,
            "poster_path": self.poster_path,
            "watched_at": self.watched_at,
        }


@dataclass
class Genre:
    """Genre from TMDB"""

    id: int
    name: str

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name}
