from selenium import webdriver
import time, json, re
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

JSON_PATH = "temp\youtube_data.json"
CSV_PATH = "temp\youtube_data.csv"
HOME_PAGE_RELATE_VIDEO_INFO_PATH = 'temp\hompage_list_video_link.json'

class DetailCrawler:
    def __init__(self, driver):
        self.driver = driver

    def extract_video_info(self):
        time.sleep(5)
        video_info = {}
        video_info["title"] = self.driver.find_element(
            "css selector", ".ytd-watch-metadata .style-scope.ytd-watch-metadata"
        ).text
        (
            video_info["channel_link"],
            video_info["channel_name"],
        ) = self._extract_channel_name_and_link()
        (
            video_info["views"],
            video_info["upload_date"],
            video_info["short_description"],
        ) = self._extract_overview_info()


        # Extract video description (ERROR)
        # description_element = self.driver.find_element("css selector", "#description-text-container yt-formatted-string")
        # description_text = description_element.get_attribute("textContent").strip()
        # video_info["description"] = description_text

        video_info["duration"] = self.driver.execute_script(
            'return document.querySelector(".ytp-time-duration").textContent;'
        )

        print()

        video_info["subcribers"] = self.driver.find_element(
            By.ID, "owner-sub-count"
        ).text

        # Extract number of likes and dislikes (Error)
        # likes_element = driver.find_element("css selector", "#top-level-buttons ytd-toggle-button-renderer:nth-child(1) button")
        # dislikes_element = driver.find_element("css selector", "#top-level-buttons ytd-toggle-button-renderer:nth-child(2) button")
        # video_info["likes"] = likes_element.text
        # video_info["dislikes"] = dislikes_element.text
        return video_info

    def extract_comments(self):
        comments = []
        comment_elements = self.driver.find_elements(By.CSS_SELECTOR, "#content-text")
        for element in comment_elements:
            comment_lines = element.text.strip().split("\n")
            comment = "\n".join(comment_lines)
            comments.append(comment)
        return comments

    def _extract_channel_name_and_link(self):
        channel_link = self.driver.find_element(
            By.XPATH, '//span[@itemprop="author"]/link'
        ).get_attribute("href")
        json_text = self.driver.find_element(
            By.XPATH, '//script[@type="application/ld+json"]'
        ).get_attribute("textContent")
        json_data = json.loads(json_text)
        channel_name = json_data["itemListElement"][0]["item"]["name"]
        return channel_link, channel_name

    def _extract_overview_info(self):
        short_description = self.driver.find_element(By.ID, "description-inner").text.strip()
        views = (
        re.search(r"([\d\.]+[KM]? views)", short_description).group(1)
        if re.search(r"([\d\.]+[KM]? views)", short_description)
        else "Views not found"
        )
        upload_date = (
            re.search(r"(\d+ [a-z]+ ago)", short_description).group(1)
            if re.search(r"(\d+ [a-z]+ ago)", short_description)
            else "Time not found"
        )
        short_description = re.split(r"([\d\.]+[KM]? views|\d+ [a-z]+ ago)", short_description)[
            -1
        ].strip()
        return views, upload_date, short_description

    def run(
        self,
        video_url,
    ):
        try:
            self.driver.get(video_url)
            time.sleep(5)

            # Scroll down to load comments
            body = self.driver.find_element("tag name", "body")
            for _ in range(10):  
                body.send_keys(Keys.PAGE_DOWN)
                time.sleep(1)

            # Extract data
            video_info = self.extract_video_info()
            comments = self.extract_comments()
            data = {
                "video_info": video_info,
                "comments": comments,
            }

            # Save the data to a JSON file
            return data
        except Exception as e:
            print("An error occurred:", str(e))

class HomePageCrawler:
    def __init__(self, driver):
        self.driver = driver
    
    def export_relate_video_info_to_json(self):
        self.save_to_json(self.get_all_relate_video_info(), HOME_PAGE_RELATE_VIDEO_INFO_PATH)
    
    def get_all_relate_video_info(self):
        self.driver.get("https://www.youtube.com")
        time.sleep(5)  

        # Scroll down to load more videos
        for _ in range(2):
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            time.sleep(3)

        video_info_list = []
        # Find all video thumbnail elements
        video_thumbnails = self.driver.find_elements("css selector", 'a#video-title-link')

        # Extract link and title values from elements
        for thumbnail in video_thumbnails:
            video_info = {
                'link': thumbnail.get_attribute('href'),
                'title': thumbnail.get_attribute('title')
            }
            video_info_list.append(video_info)
        return video_info_list
    
    def save_to_json(self, data, filename):
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=4)

class YoutubeCrawlerTool:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("detach", True)
        options.add_argument("--log-level=3")
        self.driver = webdriver.Chrome(options=options)
        self.detail_crawler = DetailCrawler(self.driver)
        self.homepage_crawler = HomePageCrawler(self.driver)
    
    def run_script1(self):
        """
        Lấy lượng lớn video link ở homepage  => Crawl dữ liệu của từng Video 
        """
        #Homepage Process 
        list_video_info = self.homepage_crawler.get_all_relate_video_info()
        self.homepage_crawler.save_to_json(list_video_info, HOME_PAGE_RELATE_VIDEO_INFO_PATH)

        #Video detail Process
        detail_list = []
        for video_info in list_video_info[1:4]:
            detail_list.append(self.detail_crawler.run(video_info['link']))
        
        self._export_to_json(detail_list)
        self.driver.quit()

    def run_script2(self, keyword_list=[]):
        """
        Tìm theo keyword => Lấy lượng lớn Video link ở màn đó 
        => Crawl dữ liệu của từng Video 
        """

        detail_list = []
        for keyword in keyword_list:
            search_url = f"https://www.youtube.com/results?search_query={keyword}"
            self.driver.get(search_url)
            self.driver.implicitly_wait(10)
            video_thumbnails = self.driver.find_elements(By.CSS_SELECTOR, 'a#video-title')
            video_links = [thumbnail.get_attribute('href') for thumbnail in video_thumbnails]
            
            try:
                detail_list.append(self.script2_scrape_video(video_links, keyword))
            except Exception:
                continue
        
        self._export_to_json(detail_list)
        self.driver.quit()

    def script2_scrape_video(self, video_links, keyword):
        data_by_keyword_dict = {keyword:[]}
        for video_link in video_links:
            data_by_keyword_dict[keyword].append(self.detail_crawler.run(video_link))
        return data_by_keyword_dict
    
    def _export_to_json(self, detail_list):
        detail_json_string = json.dumps(detail_list, indent=4)
        with open(JSON_PATH, "w", encoding="utf-8") as json_file:
            json_file.write(detail_json_string)

if __name__ == "__main__":
    tool = YoutubeCrawlerTool()
    # tool.run_script1()
    tool.run_script2(['LOL', "Hieu Thu Hai"])
