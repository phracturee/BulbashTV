"""
HTTP utilities with retry logic and better error handling
"""

import requests
import socket
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time


class RetryableSession:
    """Session with automatic retries and better error handling"""

    def __init__(self, max_retries=3, backoff_factor=0.5, timeout=30):
        self.session = requests.Session()
        self.timeout = timeout

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # Set default headers
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def get(self, url, **kwargs):
        """GET request with retries"""
        try:
            return self.session.get(url, timeout=self.timeout, **kwargs)
        except requests.exceptions.ConnectionError as e:
            print(f"[HTTP] Connection error: {e}")
            raise
        except requests.exceptions.Timeout as e:
            print(f"[HTTP] Timeout error: {e}")
            raise
        except Exception as e:
            print(f"[HTTP] Error: {e}")
            raise

    def post(self, url, **kwargs):
        """POST request with retries"""
        try:
            return self.session.post(url, timeout=self.timeout, **kwargs)
        except Exception as e:
            print(f"[HTTP] Error: {e}")
            raise


def test_dns_resolution(hostname="api.themoviedb.org"):
    """Test if hostname can be resolved"""
    try:
        ip = socket.gethostbyname(hostname)
        print(f"[DNS] {hostname} resolved to {ip}")
        return True
    except socket.gaierror as e:
        print(f"[DNS] Failed to resolve {hostname}: {e}")
        return False


def safe_request(url, max_retries=3, timeout=30, **kwargs):
    """Make a safe HTTP request with retries and fallback"""
    session = RetryableSession(max_retries=max_retries, timeout=timeout)

    for attempt in range(max_retries):
        try:
            response = session.get(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(
                    f"[HTTP] Connection failed, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(wait_time)
            else:
                raise
        except Exception:
            raise

    return None
