from bs4 import BeautifulSoup
from bs4.element import Tag, AttributeValueList
from typing import Literal

class site_info:
    url: str
    tree: list
    type: Literal["Page", "Post", "Error"]
    datePublished: str
    postId: str


    def __init__(self, html: str, url:str, tree: list):
        self.url = url
        self.tree = tree[:]
        if(not html):
            self.type = "Error"
            return
        soup = BeautifulSoup(html, "html.parser")
        postBody = soup.select_one('body[class*="postid-"]')
        self.type = "Post" if postBody else "Page"
        if not postBody:
            self.postId = None
            self.datePublished = None
        else:
            classes = postBody["class"]
            postid_list = [i for i in classes if "postid-" in i]
            self.postId = postid_list[0].split("-")[1]
            self.datePublished = soup.find_all("time", attrs={'itemprop': 'datePublished'})[0].string




class image_info:
    html: str
    tree: list
    alt: str
    src: str
    srcset: list
    name: str

    def __init__(self, img:Tag, tree:list):
        self.html = img
        self.tree = tree[:]
        self.alt = img['alt'] if img.has_attr('alt') else None
        self.class_ = img['class'] if img.has_attr('class') else None
        self.src = img['src'] if img.has_attr('src') else None
        self.srcset = img['srcset'].split(",") if img.has_attr('srcset') else None
        self.name = self.src.split('/')[-1]



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
        self.url = link['href'] if link.has_attr('href') else None
        self.tree = tree[:]
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

