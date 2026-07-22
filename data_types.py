from bs4 import BeautifulSoup
from bs4.element import Tag, AttributeValueList
from typing import Literal
from urllib.parse import urlsplit
from pathlib import PurePosixPath

class site_info:
    url: str
    tree: list
    type: Literal["Page", "Post", "Error"]
    datePublished: str
    postId: str
    extension: str
    postName: str


    def __init__(self, html: str, url:str, tree: list):
        self.url = url
        self.tree = tree[:]
        if(not html):
            self.type = "Error"
            return
        soup = BeautifulSoup(html, "html.parser")
        postBody = soup.select_one('body[class*="postid-"]')
        self.extension = PurePosixPath(urlsplit(url).path).suffix.lower()
        self.type = "Post" if postBody else "Page"
        if not postBody:
            self.postId = None
            self.datePublished = None
            self.postName = None
        else:
            classes = postBody["class"]
            postid_list = [i for i in classes if "postid-" in i]
            self.postId = postid_list[0].split("-")[1]
            self.datePublished = soup.find_all("time", attrs={'itemprop': 'datePublished'})[0].string
            self.postName = soup.find_all("h1", {'class': 'entry-title'})[0].find_next("a").string



class image_info:
    html: str
    tree: list
    alt: str
    src: str
    srcset: list
    name: str
    extension: str
    type: str
    parent_link: str

    def __init__(self, img:Tag, tree:list, soup:BeautifulSoup):
        self.html = img
        self.tree = tree[:]
        self.alt = img['alt'] if img.has_attr('alt') else None
        self.class_ = img['class'] if img.has_attr('class') else None
        self.src = img['src'] if img.has_attr('src') else None
        self.srcset = img['srcset'].split(",") if img.has_attr('srcset') else None
        self.name = self.src.split('/')[-1]
        self.extension = PurePosixPath(urlsplit(self.src).path).suffix.lower() if self.src else None
        parent = img.find_parent()
        if parent and parent.name == "article":
            self.type = "Hero"
        elif self.class_ and "wp-post-image" in self.class_ and parent and parent.name == "a":
            self.type = "Featured"
        else:
            self.type = None

        if parent.name =="a" and parent.has_attr("href"):
            self.parent_link = parent['href']
        else:
            self.parent_link = None




class link_info:
    html: str #The full html of the link
    url: str #The href of the link
    tree: list #How to get to the link
    text: str #The text that the user clicks on to click on the link
    src: str = None #The source of the link (for images)
    srcset: list = None #The source set of the link (for images)
    class_: AttributeValueList #The class(es) of the link
    type: str
    isNav : str
    extension: str

    def __init__(self, link:Tag, tree:list):
        self.html = link
        self.url = link['href'] if link.has_attr('href') else None
        self.tree = tree[:]
        self.text = link.string
        self.class_ = link['class'] if link.has_attr('class') else None
        self.extension = PurePosixPath(urlsplit(self.url).path).suffix.lower() if self.url else None
        self.type = None
        img = link.find('img')
        if img:
            self.src = img['src'] if img.has_attr('src') else None
            self.srcset = img['srcset'].split(",") if img.has_attr('srcset') else None
        if (link.find_parent('nav', attrs={'aria-label': 'Main Navigation'})):
            self.isNav = "Yes"
        else:
            self.isNav = "No"
        if(self.url and "tableau" in self.url):
            self.type = "Dashboard"

    def __str__(self):
        printed = '''Full HTML: {}
        URL: {}
        Tree: {}
        Display Text: {}
        Source: {}
        Source Set: {}
        Classes: {}'''.format(self.html, self.url, self.tree, self.text, self.src, self.srcset, self.class_)
        return printed

