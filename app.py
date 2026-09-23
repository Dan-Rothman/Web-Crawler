import requests
import time
from data_types import site_info, link_info, image_info
from bs4 import BeautifulSoup
from bs4.element import Tag
from typing import List, Any
from urllib.parse import urljoin, urlsplit, urlunsplit
from pathlib import PurePosixPath, Path
import csv
from collections import deque
import yaml


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

site_list: list[site_info] = []
link_list: list[link_info] = []
image_list: list[image_info] = []
request_timers: list[tuple[float, str]] = []
visited: set = set()
checked: set = set()
home: str
depth: int
bfs_queue = deque()
config: dict[str,Any]
excluded_extentions: frozenset[str]
search_words: frozenset[str]
counter: int
last_home_request: float = 1.0


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
    path.append(url)
    visited.add(url)
    raw_html, statusCode = fetch_page(url)
    site_list.append(site_info(statusCode, raw_html, url, path, search_words))
    if statusCode != 200:
        return
    soup = BeautifulSoup(raw_html, "html.parser")
    for img in soup.find_all('img'):
        if should_i_collect_image(img):
            image_list.append(image_info(img, path, soup))
    for link in soup.find_all('a'):
        toBeCollected = should_i_collect_link(link, url)
        href = link.get("href")
        if not href:
            if toBeCollected:
                link_list.append(link_info(link, path, None))
            continue
        href = urljoin(url, href)
        toBeCrawled = should_i_crawl(href, link, path)
        print(f"{href} should be crawled {toBeCrawled}")
        if toBeCrawled:
            bfs_queue.append((href, path[:]))
            visited.add(href)
        if(toBeCollected and not toBeCrawled and (href not in checked)):
            raw_html, statusCode = fetch_page(href)
            link_list.append(link_info(link, path, statusCode))
            checked.add(href)
        elif(toBeCollected):
            link_list.append(link_info(link, path, None))
            

def should_i_collect_image(img: Tag):
    if (img.has_attr('src') and 'data:image/svg+xml,%3Csvg' in img['src']):
        return False
    return True

def should_i_collect_link(link: Tag, url: str):
    #Don't collect main nav links from anywhere other than the home page
    if (not url==home and (link.find_parent('nav', attrs={'aria-label': 'Main Navigation'}))):
        return False
    #Same for the footer
    if (not url==home and (link.find_parent('footer', attrs={'class': 'site-footer'}))):
        return False
    #Same for the logo
    if (not url==home and (link.find_parent('header') and link.find("img", {"class": "custom-logo"}))):
        return False
    return True
    

def should_i_crawl(href:str, link: Tag, path:List) -> bool:
    #Check depth of crawl
    if(len(path) >= depth):
        return False
    #Weed out duplicate urls so there is no repeat visits
    if(href in visited or href in bfs_queue):
        return False
    #Only internal links
    if(not href.startswith(home)):
        return False
    #Don't crawl excluded file types
    extension = PurePosixPath(urlsplit(href).path).suffix.lower()
    if(excluded_extentions and (extension in excluded_extentions)):
        return False

    
    
    return True

def normalize_url(url: str) -> str:
    parts = urlsplit(url)
    normalized_path = parts.path.rstrip("/") or "/"
    return urlunsplit(
        parts.scheme.lower(),
        parts.netloc.lower(),
        normalized_path,
        parts.query,
        ""
    )





def fetch_page(url: str) -> tuple[str, int]:
    """
    Download a page and return its raw HTML as text.
    We send a User-Agent header so we don't look like some empty default bot.
    We also raise if the request failed.
    """
    try:
        global counter
        global last_home_request
        print(f"{counter} {url}")
        counter = counter + 1
        if url.startswith("mailto") or url.startswith("tel"):
            return(None, None)
        if(url.startswith(home)):
            elapsedTime = time.perf_counter() - last_home_request
            print(f"sleeping for {1-elapsedTime} seconds")
            time.sleep(max(0, 1-elapsedTime))
            last_home_request = time.perf_counter()
        start = time.perf_counter()
        response = requests.get(url, headers=HEADERS, timeout=10)
        end = time.perf_counter()
        diff = round(end - start, 2)
        request_timers.append((diff, url))
        statusCode = response.status_code
        return (response.text, statusCode)
    except Exception as e:
        with open('errors.csv', 'w', newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(f"{url} had exception {e}") 
        return ("", 999)

def load_config(config_path : str | Path) -> dict[str, Any]:
    path = Path(config_path)

    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open("r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    if not isinstance(config, dict):
        raise ValueError("The configuration file must contain a YAML mapping.")

    return config

def get_search_words(config: dict[str, Any]) -> frozenset[str]:
    try:
        configured_words = config["Search_Words"]
    except:
        return None

    if not isinstance(configured_words, list):
        raise ValueError(
            "Search_Words must be a YAML list."
        )
    print(configured_words)
    normalized_words = set()

    for word in configured_words:
        if not isinstance(word, str):
            raise ValueError(
                "Every word must be a string."
            )

        word = word.strip().lower()

        normalized_words.add(word)

    return frozenset(normalized_words)

def get_excluded_extensions(config: dict[str, Any]) -> frozenset[str]:
    try:
        configured_extensions = config["Excluded_Extensions"]
    except:
        return None

    if not isinstance(configured_extensions, list):
        raise ValueError(
            "Excluded_Extensions must be a YAML list."
        )
    print(configured_extensions)
    normalized_extensions = set()

    for extension in configured_extensions:
        if not isinstance(extension, str):
            raise ValueError(
                "Every excluded extension must be a string."
            )

        extension = extension.strip().lower()

        if not extension.startswith("."):
            extension = f".{extension}"

        normalized_extensions.add(extension)

    return frozenset(normalized_extensions)



if __name__ == "__main__":
    counter = 1
    start = time.perf_counter()

    config = load_config("config.yml")
    excluded_extentions = get_excluded_extensions(config)
    print(excluded_extentions)
    search_words = get_search_words(config)
    print(search_words)
    home = config["Home_URL"]
    print(home)
    depth = config["Maximum_Depth"]
    print(depth)
    visited = set()
    bfs_queue.append((home, []))
    while(bfs_queue):
        link_bfs()


    fields = ["URL", "Tree", "Type", "PostId", "PostName", "DatePublished", "Extension", "Status Code"]
    rows = []
    for word in search_words:
        print(word)
        fields.append("search:"+word)
        print(fields)
    print(fields)
    for site in site_list:
        row = [site.url, site.tree, site.type, site.postId, site.postName, site.datePublished, site.extension, site.statusCode]
        for word in search_words:
            row.append(site.search_word_dict[word])
        rows.append(row)

    with open('site_list.csv', 'w', newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)     # Write header
        writer.writerows(rows)  

    fields = ["HTML", "Tree", "AltText", "Source", "SourceSet", "Name", "Type", "Parent Link", "Extension"]
    rows = []
    for img in image_list:
        rows.append([img.html, img.tree, img.alt, img.src, img.srcset, img.name, img.type, img.parent_link, img.extension])
    with open('image_list.csv', 'w', newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)     # Write header
        writer.writerows(rows)

    fields = ["HTML", "URL", "Tree", "Text", "Extension", "IsNav", "Type", "Status Code", "File Size (kb)"]
    rows = []

    for link in link_list:
        rows.append([link.html, link.url, link.tree, link.text, link.extension, link.isNav, link.type, link.statusCode, link.fileSizeKB])
    with open('link_list.csv', 'w', newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)     # Write header
        writer.writerows(rows)    

    fields = ["URL", "Time Elapsed"]
    rows = []

    for request in request_timers:
        rows.append([request[1], request[0]])
    with open('request_list.csv', 'w', newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)     # Write header
        writer.writerows(rows)   

    end = time.perf_counter()
    print(len(site_list))
    print(len(image_list))
    print(len(link_list))
    print(f"Runtime: {end - start:.2f} seconds")   
    print(f"Average Request Time: {sum(x[0] for x in request_timers) / len(request_timers):.2f} seconds")