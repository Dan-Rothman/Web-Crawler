import logging
import requests
from requests import Response
import time
import data_aggregator
from utils import url_utils

logger = logging.getLogger(__name__)
last_home_request: float = 1.0


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

def get_file_size_kb(url: str, home: str, requestHead: Response):
    logger.debug("Getting file size of %s", url)
    if(url):
        url = url_utils.normalize_url(url, home)
        if url.startswith("mailto") or url.startswith("tel"):
            logger.debug("%s should not be requested", url)
            return None
    try:
        response: Response
        if(requestHead is None):
        
            response = requests.head(
                url,
                allow_redirects=True,
                timeout=10
            )
        else:
            response = requestHead


        content_length = response.headers.get("Content-Length")

        if content_length:
            kbs = int(round(int(content_length) / 1024))
            logger.debug("Got a content length of %s which will evaluate to %d kbs", content_length, kbs)
            return kbs

        logger.debug("No size found, returning none. Request head: %s", response)

    except (requests.RequestException, TypeError, ValueError):
        logger.exception("%s raised an exception", url)
        pass

    return None

def fetch_page(url: str, home:str, data_agg:data_aggregator) -> tuple[str, int]:
    """
    Download a page and return its raw HTML as text.
    We send a User-Agent header so we don't look like some empty default bot.
    We also raise if the request failed.
    """
    try:
        global last_home_request
        if url.startswith("mailto") or url.startswith("tel"):
            logger.debug("%s should not be requested", url)
            return(None, None)
        if(url.startswith(home)):
            logger.debug("%s is an internal link, starting timer to gate requests", url)
            curTime = time.perf_counter()
            logger.debug("elapsedTime is going to be %f - %f", curTime, last_home_request)
            elapsedTime = curTime - last_home_request
            logger.debug("elapsedTime is %f", elapsedTime)
            logger.debug("Sleeping for %f seconds", max(0, 1-elapsedTime))
            time.sleep(max(0, 1-elapsedTime))
            last_home_request = time.perf_counter()
        start = time.perf_counter()
        response = requests.get(url, headers=HEADERS, timeout=10)
        end = time.perf_counter()
        diff = round(end - start, 2)
        data_agg.request_timers.append((diff, url, get_file_size_kb(None, None, requestHead=response)))
        statusCode = response.status_code
        return (response.text, statusCode)
    except Exception as e:
        logger.exception("Error requesting %s", url)
        return ("", 999)