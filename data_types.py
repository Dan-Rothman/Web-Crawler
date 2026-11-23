from bs4 import BeautifulSoup
from bs4.element import Tag, AttributeValueList
from typing import Literal
from urllib.parse import urlsplit
from pathlib import PurePosixPath
import logging
import request_central
from utils import url_utils
from config import config
from request_central import fetch_page, request_info

logger = logging.getLogger(__name__)

placeholder_headers = [
            "1.1.1 Non-text Content", 
            "1.2.1 Audio-only and Video-only (Prerecorded)", 
            "1.2.2 Captions (Prerecorded)", 
            "1.2.3 Audio Description or Media Alternative (Prerecorded)", 
            "1.2.4 Captions (Live)", 
            "1.2.5 Audio Description (Prerecorded)", 
            "1.3.1 Info and Relationships", 
            "1.3.2 Meaningful Sequence", 
            "1.3.3 Sensory Characteristics", 
            "1.3.4 Orientation", 
            "1.3.5 Identify Input Purpose", 
            "1.4.1 Use of Color", 
            "1.4.2 Audio Control", 
            "1.4.3 Contrast (Minimum)", 
            "1.4.4 Resize Text", 
            "1.4.5 Images of Text", 
            "1.4.10 Reflow", 
            "1.4.11 Non-text Contrast", 
            "1.4.12 Text Spacing", 
            "1.4.13 Content on Hover or Focus", 
            "2.1.1 Keyboard", 
            "2.1.2 No Keyboard Trap", 
            "2.1.4 Character Key Shortcuts", 
            "2.2.1 Timing Adjustable", 
            "2.2.2 Pause, Stop, Hide", 
            "2.3.1 Three Flashes or Below Threshold", 
            "2.4.1 Bypass Blocks", 
            "2.4.2 Page Titled", 
            "2.4.3 Focus Order", 
            "2.4.4 Link Purpose (In Context)", 
            "2.4.5 Multiple Ways", 
            "2.4.6 Headings and Labels", 
            "2.4.7 Focus Visible", 
            "2.5.1 Pointer Gestures", 
            "2.5.2 Pointer Cancellation", 
            "2.5.3 Label in Name", 
            "2.5.4 Motion Actuation", 
            "3.1.1 Language of Page", 
            "3.1.2 Language of Parts", 
            "3.2.1 On Focus", 
            "3.2.2 On Input", 
            "3.2.3 Consistent Navigation", 
            "3.2.4 Consistent Identification", 
            "3.3.1 Error Identification", 
            "3.3.2 Labels or Instruction", 
            "3.3.3 Error Suggestion", 
            "3.3.4 Error Prevention (Legal, Financial, Data)", 
            "4.1.1 Parsing", 
            "4.1.2 Name, Role, Value", 
            "4.1.3 Status Messages"
        ]
class site_info:
    url: str
    tree: list
    type: Literal["Page", "Post", "Error"]
    tags: list[str] = []
    datePublished: str
    postId: str
    extension: str
    postName: str
    statusCode: int
    search_word_dict: dict
    meta_desc: str


    def __init__(self, requestInfo: request_info, html: str, url:str, tree: list, search_words:tuple[str]):
        self.url = url
        logger.debug("Adding %s as a site", self.url)
        self.tree = tree[:]
        self.statusCode = requestInfo.status_codes[-1]
        if(not html or self.statusCode != 200):
            self.type = "Error"
            return
        soup = BeautifulSoup(html, "html.parser")
        postBody = soup.select_one('body[class*="postid-"]')
        self.extension = PurePosixPath(urlsplit(url).path).suffix.lower()
        self.type = "Post" if postBody else "Page"
        self.tags = []
        self.search_word_dict = {}
        self.meta_desc = ""
        description_tag = soup.find("meta", attrs={"name": "description"})
        if description_tag is not None:
            self.meta_desc = description_tag.get("content", "")
            logger.debug("URL is %s\nMeta description is %s", self.url, self.meta_desc)
        for word in search_words:
            self.search_word_dict[word] =  True if word in html else False
        self.postId = None
        self.datePublished = None
        self.postName = None
        first_h1 = soup.find_all("h1")[0]
        if (first_h1):
            self.postName = first_h1.get_text()
        if postBody:
            classes = postBody["class"]
            postid_list = [i for i in classes if "postid-" in i]
            self.postId = postid_list[0].split("-")[1]
            self.datePublished = soup.find_all("time", attrs={'itemprop': 'datePublished'})[0].string
            self.postName = soup.find_all("h1", {'class': 'entry-title'})[0].find_next("a").string

    def row_headers(self) -> list[str]:
        headers = [
            "URL", 
            "Tree", 
            "Type", 
            "PostId", 
            "PostName", 
            "DatePublished", 
            "Extension", 
            "Status Code", 
            "Tags", 
            "Meta Description"
        ]
        for word in (self.search_word_dict):
            headers.append(word)

        return headers

    def rowify(self)->list[str]:
        row = [
            self.url, 
            ",".join(self.tree) if self.tree is not None else None, 
            self.type, 
            self.postId, 
            self.postName, 
            self.datePublished, 
            self.extension, 
            self.statusCode, 
            ", ".join(self.tags) if self.tags is not None else None, 
            self.meta_desc
        ]
        for word in (self.search_word_dict):
            logger.debug("rowify %s", word)
            row.append(self.search_word_dict[word])
        return row



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
    hidden: bool
    status_code: int
    requestInfo: request_info

    def __init__(self, img:Tag, tree:list, soup:BeautifulSoup, configInst:config = None, requestInfo:request_info = None):
        self.html = str(img)
        self.html = self.html.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
        self.tree = tree[:]
        self.alt = img['alt'] if img.has_attr('alt') else None
        self.class_ = img['class'] if img.has_attr('class') else None
        self.src = img['src'] if img.has_attr('src') else None
        logger.debug("Adding %s as an image", self.src)
        self.srcset = img['srcset'].split(",") if img.has_attr('srcset') else None
        self.name = self.src.split('/')[-1]
        self.extension = PurePosixPath(urlsplit(self.src).path).suffix.lower() if self.src else None
        self.hidden = True if img.find_parent("div", class_="hidden") is not None else False
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

        if requestInfo:
            self.status_code = requestInfo.status_codes[-1] 
            self.requestInfo = requestInfo 
        elif self.src and configInst:
            self.requestInfo =  fetch_page(self.src, configInst.home)
            self.status_code = self.requestInfo.status_codes[-1]  
        else:
            self.status_code = None
            self.requestInfo = None

    def should_i_collect_image(img: Tag, home:str, url:str):
        #Don't collect main nav links from anywhere other than the home page
        if (not url==home and (img.find_parent('nav', attrs={'aria-label': 'Main Navigation'}))):
            return False
        #Same for the footer
        if (not url==home and (img.find_parent('footer', attrs={'class': 'site-footer'}))):
            return False
        #Same for the logo
        if (not url==home and (img.find_parent('header'))):
            return False
        if (img.has_attr('src') and 'data:image/svg+xml,%3Csvg' in img['src']):
            return False
        return True

    def row_headers(self) -> list[str]:
        headers = [
            "HTML",
            "Tree", 
            "AltText", 
            "Source", 
            "SourceSet", 
            "Name", 
            "Type", 
            "Parent Link", 
            "Extension", 
            "Hidden",
            "Status Code"
        ]

        headers.extend(placeholder_headers)
        return headers
    
    def rowify(self)->list[str]:
        return [
            self.html, 
            ",".join(self.tree)  if self.tree is not None else None, 
            self.alt, 
            self.src, 
            self.srcset, 
            self.name, 
            self.type, 
            self.parent_link, 
            self.extension, 
            self.hidden,
            self.status_code
        ]




class link_info:
    html: str #The full html of the link
    href: str #The href of the link
    url: list[str] = [] #The href of the link
    absoluteUrl: str #The normalized url of the link
    tree: list #How to get to the link
    text: str #The text that the user clicks on to click on the link
    src: str = None #The source of the link (for images)
    srcset: list = None #The source set of the link (for images)
    class_: AttributeValueList #The class(es) of the link
    type: str
    isNav : str #Links that are in the Main Navigation header (not the logo)
    extension: str
    statusCodes: list[int]
    fileSizeKB: int
    hidden: bool
    external: bool

    def __init__(self, link:Tag, tree:list, requestInfo: request_info, configInst:config):
        self.html = str(link)
        self.html = self.html.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
        self.href = link['href'] if link.has_attr('href') else None
        if(self.href):
            logger.debug("Adding %s as a link", self.href)
        else:
            logger.debug("Adding %s as a link, no url", self.html)
        if requestInfo:
            self.url.extend(requestInfo.urls)
        else:
            self.url.append(self.href)
        self.absoluteUrl = url_utils.normalize_url(self.href, configInst.home) if self.href else None
        self.tree = tree[:]
        self.text = link.string
        self.class_ = link['class'] if link.has_attr('class') else None
        self.extension = PurePosixPath(urlsplit(self.href).path).suffix.lower() if self.href else None
        self.type = None
        self.statusCodes = requestInfo.status_codes if requestInfo else None
        self.fileSizeKB = requestInfo.file_size if requestInfo else None
        if self.extension and not self.fileSizeKB:
            self.fileSizeKB = request_central.get_file_size_kb(self.href, configInst.home, None)
        self.hidden = True if link.find_parent("div", class_="hidden") is not None else False
        img = link.find('img')
        if img:
            self.src = img['src'] if img.has_attr('src') else None
            self.srcset = img['srcset'].split(",") if img.has_attr('srcset') else None
        if (link.find_parent('nav', attrs={'aria-label': 'Main Navigation'})):
            self.isNav = "Yes"
        else:
            self.isNav = "No"
        if(self.href and "tableau" in self.href):
            self.type = "Dashboard"
        self.external = (False if self.absoluteUrl.startswith(configInst.home) or self.absoluteUrl.startswith(tuple(configInst.otherHomes)) else True) if self.url else None

    def __str__(self):
        printed = '''Full HTML: {}
        URL: {}
        Tree: {}
        Display Text: {}
        Source: {}
        Source Set: {}
        Classes: {}'''.format(self.html, self.url, self.tree, self.text, self.src, self.srcset, self.class_)
        return printed

    def should_i_collect_link(link: Tag, url: str, home:str):
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

    def row_headers(self) -> list[str]:
        headers = [
            "HTML", 
            "HREF",
            "URL", 
            "Absolute URL", 
            "Tree", 
            "Text", 
            "Extension", 
            "IsNav", 
            "Type", 
            "Status Code", 
            "File Size (kb)", 
            "Hidden", 
            "External"
        ]

        headers.extend(placeholder_headers)
        return headers

    def rowify(self)->list[str]:
        return [
            self.html, 
            self.href,
            ",".join(self.url) if self.url is not None else None, 
            self.absoluteUrl, 
            ",".join(self.tree) if self.tree is not None else None, 
            self.text, 
            self.extension, 
            self.isNav, 
            self.type, 
            ",".join(str(code) for code in self.statusCodes) if self.statusCodes is not None else None, 
            self.fileSizeKB, 
            self.hidden, 
            self.external
        ]



        


