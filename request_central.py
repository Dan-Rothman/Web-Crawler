import logging
import requests
from requests import Response
import time
from utils import url_utils

logger = logging.getLogger(__name__)
last_home_request: float = 1.0
request_index: int = 1


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

class request_info:
    status_codes: list[int] = []
    time: int
    file_size: int
    urls: list[str]
    content: str

    def __init__(self, status_codes:list[int] = None, time:int = None, file_size:int = None, urls:list[str] = None, responses:list[Response] = None, content:str = None):
        if responses:
            self.status_codes = [hop.status_code for hop in responses]
            self.urls = [hop.url for hop in responses]
        else:
            self.status_codes = status_codes
            self.urls = urls
        
        self.time = time
        self.file_size = file_size
        self.content = content


    def row_headers(self) -> list[str]:
        return [
            "URL",
            "Time Elapsed",
            "File Size (kb)",
            "Status Code",
            "Content (if small)"
        ]

    def rowify(self)->list[str]:
        return [
            ",".join(self.urls) if self.urls is not None else None,
            self.time,
            self.file_size,
            ",".join(str(code) for code in self.status_codes) if self.status_codes is not None else None,
            self.content 
        ]

def get_file_size_kb(url: str, home: str, requestHead: Response) -> tuple[int, str|None] | str | None:
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
        if response.status_code > 299:
            return None

        if content_length:
            kbs = int(round(int(content_length) / 1024))
            logger.debug("Got a content length of %s which will evaluate to %d kbs", content_length, kbs)
            if kbs < 3:
                content = (response.text)
                logger.debug("This content was very small! %s", content)
                return kbs, content
            return kbs

        logger.debug("No size found, returning none. Request head: %s", response)

    except (requests.RequestException, TypeError, ValueError):
        logger.exception("%s raised an exception", url)
        pass

    return None

def fetch_page(url: str, home:str) -> tuple[str, request_info]:
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
        responses = [*response.history, response]
        maybefilesize = get_file_size_kb(None, None, response)
        if isinstance(maybefilesize, tuple):
            size, content = maybefilesize
        elif isinstance(maybefilesize, str):
            size = maybefilesize
            content = None
        else:
            size = None
            content = None
        request = request_info(responses=responses, file_size=size, time=diff, content=content)
        return (response.text, request)
    except Exception as e:
        logger.exception("Error requesting %s", url)
        return (request_info(status_codes=[9999]), None)