from data_types import site_info, link_info, image_info
from config import config
from urllib.parse import urlsplit
import csv

class data_aggregator:
    site_list: list[site_info] = []
    link_list: list[link_info] = []
    image_list: list[image_info] = []
    request_timers: list[tuple[float, str]] = []
    posts_by_url: dict[str, site_info] = {}
    configInst: config



    def __init__(self, passedConfig):
        self.configInst = passedConfig

    def create_files(self) -> None:

        """Starting Link List Compilation"""

        fields = ["HTML", "URL", "Abolute URL", "Tree", "Text", "Extension", "IsNav", "Type", "Status Code", "File Size (kb)", "Hidden"]
        rows = []

        for link in self.link_list:
            rows.append([link.html, link.url, link.absoluteUrl, link.tree, link.text, link.extension, link.isNav, link.type, link.statusCode, link.fileSizeKB, link.hidden])
            post = self.posts_by_url.get(link.url)
            if post is None or len(link.tree) < 1:
                continue
            # The last URL must have a path like /tag/crisis/.
            path_parts = urlsplit(link.tree[-1].strip()).path.strip("/").split("/")
            if len(path_parts) == 2 and path_parts[0] == "tag" and path_parts[1]:
                tag = path_parts[1]
                if tag not in post.tags:  # Prevent duplicate tags.
                    post.tags.append(tag)
        with open('link_list.csv', 'w', newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(fields)     # Write header
            writer.writerows(rows)  


        """Starting Site List Compilation"""
        fields = ["URL", "Tree", "Type", "PostId", "PostName", "DatePublished", "Extension", "Status Code", "Tags", "Meta Description"]
        rows = []
        for word in self.configInst.search_words:
            fields.append("search:"+word)
        for site in self.site_list:
            row = [site.url, site.tree, site.type, site.postId, site.postName, site.datePublished, site.extension, site.statusCode, site.tags, site.meta_desc]
            for word in self.configInst.search_words:
                row.append(site.search_word_dict[word])
            rows.append(row)

        with open('site_list.csv', 'w', newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(fields)     # Write header
            writer.writerows(rows)  

        """Starting Image List Compilation"""

        fields = ["HTML", "Tree", "AltText", "Source", "SourceSet", "Name", "Type", "Parent Link", "Extension", "Hidden"]
        rows = []
        for img in self.image_list:
            rows.append([img.html, img.tree, img.alt, img.src, img.srcset, img.name, img.type, img.parent_link, img.extension, img.hidden])
        with open('image_list.csv', 'w', newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(fields)     # Write header
            writer.writerows(rows)  

        fields = ["URL", "Time Elapsed"]
        rows = []

        for request in self.request_timers:
            rows.append([request[1], request[0]])
        with open('request_list.csv', 'w', newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(fields)     # Write header
            writer.writerows(rows) 


        fields = ["Tags", "Count"]
        rows = []
        tagQuantity: dict[str, int] = {}

        for site in self.site_list:
            for tag in site.tags:
                if(tag in tagQuantity):
                    tagQuantity[tag] = tagQuantity[tag] + 1
                else:
                    tagQuantity[tag] = 1

        for tag in tagQuantity:
            rows.append([tag, tagQuantity[tag]])

        with open('tag_list.csv', 'w', newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(fields)     # Write header
            writer.writerows(rows)  
