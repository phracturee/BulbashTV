# Changelog

All notable changes to BulbashTV will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security
- Added Content Security Policy (CSP) headers
- Added X-Frame-Options, X-Content-Type-Options, X-XSS-Protection headers
- Implemented magnet link validation to prevent command injection
- Added input validation for all API endpoints
- Added search query sanitization
- Updated dependencies with security patches (urllib3, certifi, cryptography)

### Added
- Skip navigation link for accessibility
- ARIA labels for icon-only buttons
- Focus trap for modal dialogs
- Screen reader announcements for dynamic content
- Visible focus indicators
- Input validation functions (validate_magnet_link, validate_search_query, validate_episode_pattern)
- Security headers middleware

### Changed
- Improved log file rotation (10MB max, 5 backups)
- Separated torrent statistics and MPV progress logs
- Enhanced error handling in API endpoints

### Fixed
- Fixed log output mixing MPV and torrent statistics
- Fixed accessibility issues with progress bars
- Fixed missing ARIA attributes on interactive elements

---

## [1.0.0] - 2025-03-23

### Added
- Initial release
- TMDB API integration for movie/TV show metadata
- Multi-tracker torrent search (RuTracker, Rutor, LostFilm)
- Torrent streaming via webtorrent-cli + mpv
- Favorites management with folders
- Watch history tracking
- Search history
- Image caching for posters/backdrops
- Selected torrent prioritization
- TV show season/episode browsing
- Russian language support

### Technical Stack
- Backend: Python 3.9+, Flask 3.0+
- Frontend: HTML templates, vanilla JavaScript
- Torrent: webtorrent-cli 5.1.3, mpv
- Data: JSON files (favorites, history, cache)

---

## Version History Summary

| Version | Date | Key Changes |
|---------|------|-------------|
| Unreleased | 2026-03-23 | Security hardening, accessibility improvements |
| 1.0.0 | 2025-03-23 | Initial release |

---

## Upcoming Features

### Planned
- [ ] User authentication system
- [ ] Database support (SQLite/PostgreSQL) instead of JSON files
- [ ] Rate limiting for API endpoints
- [ ] Docker Compose configuration
- [ ] Automated testing suite
- [ ] CI/CD pipeline integration
- [ ] WebSocket support for real-time status updates
- [ ] Logo/branding design
- [ ] LostFilm parser integration
- [ ] Noname parser integration

### Under Consideration
- [ ] Multi-user support with profiles
- [ ] Watchlist feature
- [ ] Recommendations based on watch history
- [ ] Social features (share favorites)
- [ ] Plugin system for additional trackers

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## Security

If you discover a security vulnerability, please report it responsibly:
1. **Do not** create a public GitHub issue
2. Email: phracture266@gmail.com
3. Allow reasonable time for disclosure and patching

## License

This project is created for educational purposes.
