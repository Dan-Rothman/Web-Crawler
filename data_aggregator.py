from data_types import site_info, link_info, image_info
from config import config
from urllib.parse import urlsplit
import csv

class data_aggregator:
    site_list: list[site_info] = []
    link_list: list[link_info] = []
    image_list: list[image_info] = []
    request_timers: list[tuple[float, str, str]] = []
    posts_by_url: dict[str, site_info] = {}
    configInst: config



    def __init__(self, passedConfig):
        self.configInst = passedConfig

    def create_files(self) -> None:

        """Starting Link List Compilation"""

        fields = ["HTML", "URL", "Abolute URL", "Tree", "Text", "Extension", "IsNav", "Type", "Status Code", "File Size (kb)", "Hidden", "External", "1.1.1 Non-text Content", "1.2.1 Audio-only and Video-only (Prerecorded)", "1.2.2 Captions (Prerecorded)", "1.2.3 Audio Description or Media Alternative (Prerecorded)", "1.2.4 Captions (Live)", "1.2.5 Audio Description (Prerecorded)", "1.3.1 Info and Relationships", "1.3.2 Meaningful Sequence", "1.3.3 Sensory Characteristics", "1.3.4 Orientation", "1.3.5 Identify Input Purpose", "1.4.1 Use of Color", "1.4.2 Audio Control", "1.4.3 Contrast (Minimum)", "1.4.4 Resize Text", "1.4.5 Images of Text", "1.4.10 Reflow", "1.4.11 Non-text Contrast", "1.4.12 Text Spacing", "1.4.13 Content on Hover or Focus", "2.1.1 Keyboard", "2.1.2 No Keyboard Trap", "2.1.4 Character Key Shortcuts", "2.2.1 Timing Adjustable", "2.2.2 Pause, Stop, Hide", "2.3.1 Three Flashes or Below Threshold", "2.4.1 Bypass Blocks", "2.4.2 Page Titled", "2.4.3 Focus Order", "2.4.4 Link Purpose (In Context)", "2.4.5 Multiple Ways", "2.4.6 Headings and Labels", "2.4.7 Focus Visible", "2.5.1 Pointer Gestures", "2.5.2 Pointer Cancellation", "2.5.3 Label in Name", "2.5.4 Motion Actuation", "3.1.1 Language of Page", "3.1.2 Language of Parts", "3.2.1 On Focus", "3.2.2 On Input", "3.2.3 Consistent Navigation", "3.2.4 Consistent Identification", "3.3.1 Error Identification", "3.3.2 Labels or Instruction", "3.3.3 Error Suggestion", "3.3.4 Error Prevention (Legal, Financial, Data)", "4.1.1 Parsing", "4.1.2 Name, Role, Value", "4.1.3 Status Messages"]
        rows = []

        for link in self.link_list:
            rows.append([link.html, link.url, link.absoluteUrl, link.tree, link.text, link.extension, link.isNav, link.type, link.statusCode, link.fileSizeKB, link.hidden, link.external])
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

        fields = ["HTML", "Tree", "AltText", "Source", "SourceSet", "Name", "Type", "Parent Link", "Extension", "Hidden", "1.1.1 Non-text Content", "1.2.1 Audio-only and Video-only (Prerecorded)", "1.2.2 Captions (Prerecorded)", "1.2.3 Audio Description or Media Alternative (Prerecorded)", "1.2.4 Captions (Live)", "1.2.5 Audio Description (Prerecorded)", "1.3.1 Info and Relationships", "1.3.2 Meaningful Sequence", "1.3.3 Sensory Characteristics", "1.3.4 Orientation", "1.3.5 Identify Input Purpose", "1.4.1 Use of Color", "1.4.2 Audio Control", "1.4.3 Contrast (Minimum)", "1.4.4 Resize Text", "1.4.5 Images of Text", "1.4.10 Reflow", "1.4.11 Non-text Contrast", "1.4.12 Text Spacing", "1.4.13 Content on Hover or Focus", "2.1.1 Keyboard", "2.1.2 No Keyboard Trap", "2.1.4 Character Key Shortcuts", "2.2.1 Timing Adjustable", "2.2.2 Pause, Stop, Hide", "2.3.1 Three Flashes or Below Threshold", "2.4.1 Bypass Blocks", "2.4.2 Page Titled", "2.4.3 Focus Order", "2.4.4 Link Purpose (In Context)", "2.4.5 Multiple Ways", "2.4.6 Headings and Labels", "2.4.7 Focus Visible", "2.5.1 Pointer Gestures", "2.5.2 Pointer Cancellation", "2.5.3 Label in Name", "2.5.4 Motion Actuation", "3.1.1 Language of Page", "3.1.2 Language of Parts", "3.2.1 On Focus", "3.2.2 On Input", "3.2.3 Consistent Navigation", "3.2.4 Consistent Identification", "3.3.1 Error Identification", "3.3.2 Labels or Instruction", "3.3.3 Error Suggestion", "3.3.4 Error Prevention (Legal, Financial, Data)", "4.1.1 Parsing", "4.1.2 Name, Role, Value", "4.1.3 Status Messages"]
        rows = []
        for img in self.image_list:
            rows.append([img.html, img.tree, img.alt, img.src, img.srcset, img.name, img.type, img.parent_link, img.extension, img.hidden])
        with open('image_list.csv', 'w', newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(fields)     # Write header
            writer.writerows(rows)  

        fields = ["URL", "Time Elapsed", "File Size"]
        rows = []

        for request in self.request_timers:
            rows.append([request[1], request[0], request[2]])
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
