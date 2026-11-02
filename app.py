import time
from bs4 import BeautifulSoup
from bs4.element import Tag
from collections import deque
from typing import List
import sys, logging
from rich.console import Console
from pathlib import PurePosixPath
from urllib.parse import urlsplit

from config import config
from data_aggregator import data_aggregator
from data_types import site_info, link_info, image_info
from utils import url_utils
import request_central

visited: set = set()
checked: set = set()
configInst: config = config()
dataAgg: data_aggregator = data_aggregator(configInst)
bfs_queue = deque()
counter: int


def link_bfs():
    """Takes the raw html from fetch_page, and burrows down to visit all the internal links
    that are navigatable from the given html. Maintains a queue that represents the path that was taken
    to get to the current link"""
    """print(url)
    print(len(visited))
    print(queue)
    input("Press Enter to continue...")"""

    """
    url is the full url of the site
    path is a list of urls in order of what you'd have to click on to get to the current url, not including the current url
    visited is a set of urls that have been processed by link_bfs. All should appear in site list
    raw_html is a string representing all of the html recieved from fetching the current url
    status_code is what status code we got from fetching that page
    """
    url, path = bfs_queue.popleft()
    if(len(bfs_queue) > 0):
        next_url, _ = bfs_queue[0]
        logger.debug("New head of the queue is %s", next_url)
    path.append(url)
    visited.add(url)
    raw_html, statusCode = request_central.fetch_page(url, configInst.home, dataAgg)
    site = site_info(statusCode, raw_html, url, path, configInst.search_words)
    dataAgg.site_list.append(site)
    if(site.type == "Post"):
        logger.debug("%s is being added to Posts", site.url)
        dataAgg.posts_by_url[site.url] = site
    if statusCode != 200:
        logger.debug("%s errored out with status code %s", url, statusCode)
        return
    soup = BeautifulSoup(raw_html, "html.parser")
    for img in soup.find_all('img'):
        if image_info.should_i_collect_image(img, configInst.home, url):
            dataAgg.image_list.append(image_info(img, path, soup))
    for link in soup.find_all('a'):
        toBeCollected = link_info.should_i_collect_link(link, url, configInst.home)
        href = link.get("href")
        if not href:
            if toBeCollected:
                dataAgg.link_list.append(link_info(link, path, None, configInst.home))
            continue
        href = url_utils.normalize_url(href, configInst.home)
        toBeCrawled = should_i_crawl(href, link, path)
        if toBeCrawled:
            bfs_queue.append((url_utils.normalize_url(href, configInst.home), path[:]))
            visited.add(href)
        if(toBeCollected and not toBeCrawled and url_utils.not_seen(href, checked, visited, bfs_queue, configInst.home)):
            raw_html, statusCode = request_central.fetch_page(href, configInst.home, dataAgg)
            dataAgg.link_list.append(link_info(link, path, statusCode, configInst.home))
            checked.add(href)
        elif(toBeCollected):
            dataAgg.link_list.append(link_info(link, path, None, configInst.home))

def should_i_crawl(href:str, link: Tag, path:List) -> bool:
    #Check depth of crawl
    href = url_utils.normalize_url(href, configInst.home)
    if(len(path) >= configInst.depth):
        logger.debug("%s should not be crawled because it is too deep", href)
        return False
    #Weed out duplicate urls so there is no repeat visits
    if(href in visited or href in bfs_queue):
        logger.debug("%s should not be crawled because it has already been crawled or will be crawled", href)
        return False
    #Only internal links
    if(not href.startswith(configInst.home)):
        logger.debug("%s should not be crawled because it is not an internal link", href)
        return False
    #Don't crawl excluded file types
    extension = PurePosixPath(urlsplit(href).path).suffix.lower()
    if(configInst.excluded_extentions and (extension in configInst.excluded_extentions)):
        logger.debug("%s should not be crawled because it has an excluded extention (%s)", href, extension)
        return False

    
    logger.debug("%s should be crawled, add it to the queue", href)
    return True
            

if __name__ == "__main__":
    loggingMode = "log" in sys.argv[1:]
    logFile = "crawler.log"

    logging.basicConfig(
    filename=logFile if loggingMode else None,
    filemode="w",  # Start a fresh log each run
    level=logging.DEBUG if loggingMode else logging.WARNING,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    )

    logger = logging.getLogger(__name__)
    if loggingMode:
        print("Starting log in %s" % logFile)

    start = time.perf_counter()
    bfs_queue.append((configInst.home, []))
    console = Console()
    with console.status(status="Crawling site...", spinner="dots") as status:
        while(bfs_queue):
            next_url, _ = bfs_queue[0]
            status.update(f"Checking {next_url}")
            link_bfs()

    dataAgg.create_files()

    end = time.perf_counter()
    print(len(dataAgg.site_list))
    print(len(dataAgg.image_list))
    print(len(dataAgg.link_list))
    print(f"Runtime: {end - start:.2f} seconds")   
    print(f"Average Request Time: {sum(x[0] for x in dataAgg.request_timers) / len(dataAgg.request_timers):.2f} seconds")

