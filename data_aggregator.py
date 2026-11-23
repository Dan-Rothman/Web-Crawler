from data_types import site_info, link_info, image_info
from request_central import request_info
from config import config
from urllib.parse import urlsplit
import csv
import logging

logger = logging.getLogger(__name__)
class data_aggregator:
    site_list: list[site_info] = []
    link_list: list[link_info] = []
    image_list: list[image_info] = []
    request_list: list[request_info] = []
    posts_by_url: dict[str, site_info] = {}
    configInst: config



    def __init__(self, passedConfig):
        self.configInst = passedConfig

    def create_files(self) -> None:

        """Starting Link List Compilation"""
        if len(self.link_list) > 0:
            fields = self.link_list[0].row_headers()
            rows = []

            for link in self.link_list:
                rows.append(link.rowify())
                post = self.posts_by_url.get(link.absoluteUrl)
                if post is None or len(link.tree) < 1:
                    logger.debug("%s is not found in the posts dictionary.\nWould %s be a better identifier?", link.absoluteUrl, link.url[-1])
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
        if len(self.site_list) > 0:
            fields = self.site_list[0].row_headers()
            rows = []
            for site in self.site_list:
                rows.append(site.rowify())

            with open('site_list.csv', 'w', newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(fields)     # Write header
                writer.writerows(rows)  

        """Starting Image List Compilation"""

        if len(self.image_list) > 0:
            fields = self.image_list[0].row_headers()
            rows = []
            for img in self.image_list:
                rows.append(img.rowify())
            with open('image_list.csv', 'w', newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(fields)     # Write header
                writer.writerows(rows)  

        """Starting Request List Compilation"""

        if len(self.request_list) > 0:
            fields = self.request_list[0].row_headers()
            rows = []

            for request in self.request_list:
                rows.append(request.rowify())
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
