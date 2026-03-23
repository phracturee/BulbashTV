# Contributing to BulbashTV

Thank you for considering contributing to BulbashTV! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Pull Requests](#pull-requests)
- [Coding Standards](#coding-standards)
  - [Python Style Guide](#python-style-guide)
  - [JavaScript Style Guide](#javascript-style-guide)
  - [HTML/CSS Guidelines](#htmlcss-guidelines)
- [Testing](#testing)
- [Security](#security)
- [Pull Request Process](#pull-request-process)

---

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Welcome newcomers and help them learn
- Keep discussions professional and on-topic

---

## Getting Started

1. **Fork** the repository
2. **Clone** your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/BulbashTV.git
   cd BulbashTV
   ```
3. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## Development Setup

### Prerequisites

- Python 3.9+
- Node.js 16+
- mpv media player
- TMDB API key

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install

# Copy configuration
cp config.py.example config.py
# Edit config.py with your TMDB API key
```

### Running in Development

```bash
# Start Flask app
python app.py

# Access at http://localhost:5000
```

---

## How to Contribute

### Reporting Bugs

Before creating bug reports:
- Check existing issues to avoid duplicates
- Gather information (error messages, steps to reproduce, environment details)

**Good Bug Report Example:**
```markdown
**Describe the bug**
Torrent search returns 0 results for Russian queries.

**To Reproduce**
1. Go to search page
2. Enter "Матрица" in Cyrillic
3. Click search
4. See no results

**Expected behavior**
Should return results from RuTracker and Rutor.

**Environment:**
- OS: Ubuntu 22.04
- Python: 3.10.6
- Browser: Firefox 115

**Additional context**
Works fine with English queries like "Matrix".
```

### Suggesting Features

Before suggesting features:
- Check if feature already exists or is planned
- Consider scope and complexity

**Good Feature Request Example:**
```markdown
**Is your feature request related to a problem?**
I'm frustrated that I can't filter search results by quality (4K, 1080p, etc.).

**Describe the solution you'd like**
Add quality filter dropdown in search results page with options:
- All qualities
- 4K/UHD
- 1080p
- 720p
- Other

**Describe alternatives you've considered**
Manual filtering by reading each torrent title.

**Additional context**
Quality filtering would improve user experience, especially for users with bandwidth/storage constraints.
```

### Pull Requests

1. **Fork** and create branch
2. **Make changes** following coding standards
3. **Test** your changes
4. **Update documentation** if needed
5. **Submit PR** with clear description

---

## Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/)
- Use type hints for function signatures
- Add docstrings for public methods
- Keep functions focused (single responsibility)

**Example:**
```python
def validate_magnet_link(magnet: str) -> bool:
    """
    Validate magnet link format and check for dangerous characters.
    
    Args:
        magnet: Magnet link string
        
    Returns:
        bool: True if valid, False otherwise
        
    Raises:
        None
    """
    if not magnet or not isinstance(magnet, str):
        return False
    
    # Implementation...
```

**Do:**
- Use descriptive variable names
- Add error handling
- Log security-relevant events
- Write unit tests for new functions

**Don't:**
- Use `os.system()` - use `subprocess` instead
- Hardcode secrets (use environment variables)
- Skip input validation
- Write functions longer than 50 lines

### JavaScript Style Guide

- Use `const` and `let` (no `var`)
- Use arrow functions for callbacks
- Add JSDoc comments for public functions
- Handle errors gracefully

**Example:**
```javascript
/**
 * Toggle favorite status for media item
 * @param {number} itemId - TMDB item ID
 * @param {string} mediaType - 'movie' or 'tv'
 * @returns {Promise<boolean>} Success status
 */
async function toggleFavorite(itemId, mediaType) {
    try {
        const response = await fetch('/api/favorites/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({item_id: itemId, media_type: mediaType})
        });
        return response.ok;
    } catch (error) {
        console.error('[Favorite] Error:', error);
        return false;
    }
}
```

### HTML/CSS Guidelines

- Use semantic HTML elements
- Add ARIA attributes for accessibility
- Follow BEM naming for CSS classes
- Ensure color contrast meets WCAG AA

**Example:**
```html
<!-- Good -->
<button 
    class="favorite-btn"
    aria-label="Добавить в избранное: {{ item.title }}"
    aria-pressed="{{ 'true' if item.is_favorite else 'false' }}">
    <i class="fas fa-heart" aria-hidden="true"></i>
</button>

<!-- Bad -->
<div onclick="toggleFavorite()" class="btn">❤️</div>
```

---

## Testing

### Running Tests

```bash
# Python syntax check
python -m py_compile app.py services/*.py

# Type checking (if using mypy)
mypy app.py services/

# JavaScript linting
npx eslint static/js/
```

### Writing Tests

```python
import unittest
from app import BulbashTVApp

class TestInputValidation(unittest.TestCase):
    def setUp(self):
        self.app = BulbashTVApp()
        self.client = self.app.app.test_client()
    
    def test_valid_magnet_link(self):
        """Test valid magnet link passes validation"""
        magnet = "magnet:?xt=urn:btih:08ada5a7a6183aae1e09d831df6748d566095a10"
        result = self.app.validate_magnet_link(magnet)
        self.assertTrue(result)
    
    def test_dangerous_magnet_link(self):
        """Test magnet link with shell injection fails"""
        magnet = "magnet:?xt=urn:btih:08ada5a7a6183aae1e09d831df6748d566095a10; rm -rf /"
        result = self.app.validate_magnet_link(magnet)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
```

---

## Security

### Security Guidelines

- **Never** commit sensitive data (API keys, passwords, cookies)
- **Always** validate and sanitize user input
- **Use** parameterized queries (if using SQL)
- **Enable** security headers (CSP, X-Frame-Options)
- **Keep** dependencies updated

### Reporting Security Vulnerabilities

**DO NOT** create public issues for security vulnerabilities.

Instead:
1. Email: phracture266@gmail.com
2. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)
3. Allow 30 days for patch before public disclosure

---

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] No security issues introduced
- [ ] No breaking changes (or documented)

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix/feature requiring version bump)
- [ ] Documentation update

## Testing
- [ ] Tested locally
- [ ] Unit tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project guidelines
- [ ] Self-reviewed code
- [ ] Commented complex code
- [ ] Updated documentation
- [ ] No new warnings
- [ ] Tested on different browsers (if UI change)

## Related Issues
Closes #123
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests
2. **Code Review**: Maintainer reviews code
3. **Changes**: Address review feedback
4. **Merge**: Maintainer merges PR

---

## Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [TMDB API Documentation](https://developers.themoviedb.org/3)
- [WebTorrent Documentation](https://webtorrent.io/docs)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [OWASP Security Cheatsheets](https://cheatsheetseries.owasp.org/)

---

## Questions?

Feel free to open an issue with the "question" label for any questions about contributing.

For other inquiries, contact: phracture266@gmail.com

Thank you for contributing to BulbashTV! 🎬
