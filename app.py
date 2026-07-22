import requests
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
visited: set = set()
home: str
depth: int
bfs_queue = deque()
config: dict[str,Any]
excluded_extentions: frozenset[str]


def link_bfs():
    """Takes the raw html from fetch_page, and burrows down to visit all the internal links
    that are navigatable from the given html. Maintains a queue that represents the path that was taken
    to get to the current link"""
    """print(url)
    print(len(visited))
    print(queue)
    input("Press Enter to continue...")"""
    url, path = bfs_queue.popleft()
    path.append(url)
    visited.add(url)
    try:
        raw_html = fetch_page(url)
    except:
        site_list.append(site_info(None, url, path))
        return
    site_list.append(site_info(raw_html, url, path))
    soup = BeautifulSoup(raw_html, "html.parser")
    for img in soup.find_all('img'):
        if should_i_collect_image(img):
            image_list.append(image_info(img, path))
    for link in soup.find_all('a'):
        if should_i_collect_link(link, url):
            link_list.append(link_info(link, path))
        href = link.get("href")
        if not href:
            continue
        href = urljoin(url, href)
        if should_i_crawl(href, link, path):
            bfs_queue.append((href, path[:]))
            visited.add(href)

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





def fetch_page(url: str) -> str:
    """
    Download a page and return its raw HTML as text.
    We send a User-Agent header so we don't look like some empty default bot.
    We also raise if the request failed.
    """
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.text

def load_config(config_path : str | Path) -> dict[str, Any]:
    path = Path(config_path)

    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open("r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    if not isinstance(config, dict):
        raise ValueError("The configuration file must contain a YAML mapping.")

    return config

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
    config = load_config("config.yml")
    excluded_extentions = get_excluded_extensions(config)
    print(excluded_extentions)
    home = config["Home_URL"]
    print(home)
    depth = config["Maximum_Depth"]
    print(depth)
    visited = set()
    bfs_queue.append((home, []))
    while(bfs_queue):
        link_bfs()
    print(len(site_list))
    print(len(image_list))
    print(len(link_list))


    fields = ["URL", "Tree", "Type", "PostId", "DatePublished"]
    rows = []
    for site in site_list:
        rows.append([site.url, site.tree, site.type, site.postId, site.datePublished])
    with open('site_list.csv', 'w', newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)     # Write header
        writer.writerows(rows)  

    fields = ["HTML", "Tree", "AltText", "Source", "SourceSet", "Name"]
    rows = []
    for img in image_list:
        rows.append([img.html, img.tree, img.alt, img.src, img.srcset, img.name])
    with open('image_list.csv', 'w', newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)     # Write header
        writer.writerows(rows)

    fields = ["HTML", "URL", "Tree", "Text"]
    rows = []

    for link in link_list:
        rows.append([link.html, link.url, link.tree, link.text])
    with open('link_list.csv', 'w', newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)     # Write header
        writer.writerows(rows)       