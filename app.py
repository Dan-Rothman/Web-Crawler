import requests
import data_types
from data_types import site_info, link_info, image_info
from bs4 import BeautifulSoup
from typing import List, Tuple
import csv
import sys


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
home: str = "https://analytics.alleghenycounty.us/"
depth: int


def link_dfs(url: str, queue: list):
    """Takes the raw html from fetch_page, and burrows down to visit all the internal links
    that are navigatable from the given html. Maintains a queue that represents the path that was taken
    to get to the current link"""
    """print(url)
    print(len(visited))
    print(queue)
    input("Press Enter to continue...")"""
    queue.append(url)
    visited.add(url)
    raw_html = fetch_page(url)
    site_list.append(site_info(raw_html, url, queue))
    soup = BeautifulSoup(raw_html, "html.parser")
    for img in soup.find_all('img'):
        if not (img.has_attr('src') and 'data:image/svg+xml,%3Csvg' in img['src']):
            image_list.append(image_info(img, queue))
    for link in soup.find_all('a'):
        link_list.append(link_info(link, queue))
        if(((len(queue)<depth) and not link['href'] in visited and link['href'].startswith(home) and not link['href'].endswith(".docx")) and not (not url==home and link.find_parent('nav', attrs={'aria-label': 'Main Navigation'}))):
            link_dfs(link['href'], queue)
    queue.pop()




def fetch_page(url: str) -> str:
    """
    Download a page and return its raw HTML as text.
    We send a User-Agent header so we don't look like some empty default bot.
    We also raise if the request failed.
    """
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.text



if __name__ == "__main__":
    visited = set()
    depth = int(sys.argv[1])
    link_dfs(home, [])
    print(len(site_list))
    print(len(image_list))
    print(len(link_list))


    fields = ["URL", "Tree", "Type", "PostId"]
    rows = []
    for site in site_list:
        rows.append([site.url, site.tree, site.type, site.postId])
    with open('site_list.csv', 'w', newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(fields)     # Write header
        writer.writerows(rows)  

    fields = ["HTML", "Tree", "AltText", "Source", "SourceSet"]
    rows = []
    for img in image_list:
        rows.append([img.html, img.tree, img.alt, img.src, img.srcset])
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



# 💡 Example: Using ScrapingBee's premium proxy instead of direct requests.
# Replace `fetch_page()` with the snippet below to fetch pages via ScrapingBee's API.
# This helps when sites block requests or require proxy rotation.

"""
def fetch_page(url: str) -> str:
    API_KEY = "YOUR_SCRAPINGBEE_API_KEY"
    api_url = "https://app.scrapingbee.com/api/v1"
    params = {
        "api_key": API_KEY,
        "url": url,
        "premium_proxy": True,   # enables premium proxy routing
        "render_js": False,      # set to true for JS-heavy sites
    }

    response = requests.get(api_url, params=params, timeout=30)
    response.raise_for_status()
    return response.text
"""