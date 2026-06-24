import requests
from bs4 import BeautifulSoup
from typing import List, Tuple


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


def fetch_page(url: str) -> str:
    """
    Download a page and return its raw HTML as text.
    We send a User-Agent header so we don't look like some empty default bot.
    We also raise if the request failed.
    """
    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    return response.text

def parse_front_page(html: str) -> List[Tuple[str, str]]:
    """
    Parse the Hacker News front page HTML and extract (title, link)
    for each story.
    """
    soup = BeautifulSoup(html, "html.parser")

    # each story title lives in a <span class="titleline">
    title_nodes = soup.select(".titleline")

    items: List[Tuple[str, str]] = []

    for node in title_nodes:
        main_link = node.find("a")
        if not main_link:
            continue

        title = main_link.get_text(strip=True)
        href = main_link.get("href", "")

        items.append((title, href))

    return items

def crawl_hacker_news() -> None:
    """
    Fetch the Hacker News homepage, grab the first 10 stories,
    and print them in a clean format.
    """
    url = "https://news.ycombinator.com/"
    html = fetch_page(url)
    stories = parse_front_page(html)

    for i, (title, href) in enumerate(stories[:10], start=1):
        print(f"{i}. {title} → {href}")


if __name__ == "__main__":
    crawl_hacker_news()

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