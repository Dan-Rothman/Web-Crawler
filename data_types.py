from bs4 import BeautifulSoup
from bs4.element import Tag, AttributeValueList
from typing import Literal

class site_info:
    url: str
    tree: list
    type: Literal["Image", "Page", "Post"]

    def __init__(self, html: str, url:str, tree: list):
        self.url = url
        self.tree = tree

class image_info:
    pass

class link_info:
    html: str #The full html of the link
    url: str #The href of the link
    tree: list #How to get to the link
    text: str #The text that the user clicks on to click on the link
    src: str = None #The source of the link (for images)
    srcset: list = None #The source set of the link (for images)
    class_: AttributeValueList #The class(es) of the link

    def __init__(self, link:Tag, tree:list):
        self.html = link
        self.url = link['href']
        self.tree = tree
        self.text = link.string
        self.class_ = link['class'] if link.has_attr('class') else None
        img = link.find('img')
        if img:
            self.src = img['src'] if img.has_attr('src') else None
            self.srcset = img['srcset'].split(",") if img.has_attr('srcset') else None

    def __str__(self):
        printed = '''Full HTML: {}
        URL: {}
        Tree: {}
        Display Text: {}
        Source: {}
        Source Set: {}
        Classes: {}'''.format(self.html, self.url, self.tree, self.text, self.src, self.srcset, self.class_)
        return printed

