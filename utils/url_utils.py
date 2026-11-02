import logging
from urllib.parse import urljoin, urlsplit, urlunsplit
from collections import deque


logger = logging.getLogger(__name__)

def not_seen(url: str, checked: set, visited:set, bfs_queue:deque, home:str) -> bool:
    url = normalize_url(url, home)
    if(url in checked):
        return False
    if(url in visited):
        return False
    if(url in bfs_queue):
        return False
    return True

def normalize_url(url: str, home: str) -> str:
    logger.debug("Normalizing the url %s", url)
    url = url.strip()
    absolute_url = urljoin(home, url)
    parts = urlsplit(absolute_url)
    normalized_url = urlunsplit(
        parts._replace(path=parts.path.rstrip("/") + "/")
    )
    logger.debug("Normalized url: %s", normalized_url)
    return normalized_url

