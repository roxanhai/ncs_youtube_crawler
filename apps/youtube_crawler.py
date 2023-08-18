from selenium import webdriver
import time, json, re
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import datetime
from crawler_logger import CrawlerLogger
from decorators import timing_decorator

JSON_PATH = "temp\youtube_data.json"
CSV_PATH = "temp\youtube_data.csv"
HOME_PAGE_RELATE_VIDEO_INFO_PATH = "temp\hompage_list_video_link.json"
YOUTUBE_HOMEPAGE_URL = "https://www.youtube.com"
BROWSER_LANGUAGE = "en"
crawler_logger = CrawlerLogger()


class DetailCrawler:
    def __init__(self, driver):
        self.driver = driver

    def scroll_down_action(self, amount):
        body = self.driver.find_element("tag name", "body")
        for _ in range(amount):
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(1)

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
            _,  # Old Views
            _,  # Old Upload time
            video_info["short_description"],
        ) = self._extract_overview_info()

        (
            video_info["views_number"],
            video_info["upload_date"],
        ) = self._extract_views_and_upload_info()
        # Extract video description (ERROR)
        # description_element = self.driver.find_element("css selector", "#description-text-container yt-formatted-string")
        # description_text = description_element.get_attribute("textContent").strip()
        # video_info["description"] = description_text

        video_info["duration"] = self.driver.execute_script(
            'return document.querySelector(".ytp-time-duration").textContent;'
        )

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
        comment_elements = self.driver.find_elements(By.CSS_SELECTOR, "#body")
        comments_data = []
        for comment in comment_elements:
            try:
                author_element = comment.find_element(By.CSS_SELECTOR, "#author-text")
                comment_time_element = comment.find_element(
                    By.CSS_SELECTOR, "#header .published-time-text a"
                )
                comment_text_element = comment.find_element(
                    By.CSS_SELECTOR, "#content-text"
                )
                author_id = author_element.get_attribute("href").split("/")[-1]
                author_name = author_element.text
                author_link = author_element.get_attribute("href")
                comment_time = comment_time_element.text
                comment_text = comment_text_element.text

                comments_data.append(
                    {
                        "author_id": author_id,
                        "author_name": author_name,
                        "author_link": author_link,
                        "comment_time": comment_time,
                        "comment": comment_text,
                    }
                )
            except Exception as e:
                crawler_logger.error(str(e))

        return comments_data

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
        short_description = self.driver.find_element(
            By.ID, "description-inner"
        ).text.strip()
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
        short_description = re.split(
            r"([\d\.]+[KM]? views|\d+ [a-z]+ ago)", short_description
        )[-1].strip()
        return views, upload_date, short_description

    def detech_views_and_upload_info(self, context):
        EN_pattern = r"([\d,]+)\s+views\s+•\s+(?:Premiered\s+)?([A-Za-z]{3})\s+(\d{1,2}),\s+(\d{4})"
        VN_pattern = r"([\d,.]+)\s+lượt xem\s+•\s+(?:Đã công chiếu vào )?(\d{1,2})\s+thg\s+(\d{1,2}),\s+(\d{4})"

        match = re.search(EN_pattern, context, re.UNICODE)
        if match:
            views = match.group(1).replace(",", "")
            day = match.group(3)
            month_abbr = match.group(2)
            year = int(match.group(4))
            month_number = datetime.datetime.strptime(month_abbr, "%b").month
            date = f"{day.zfill(2)}/{month_number:02d}/{year}"
            return views, date
        else:
            new_match = re.search(VN_pattern, context, re.UNICODE)
            if new_match:
                views = new_match.group(1).replace(",", "")
                day = new_match.group(2)
                month = new_match.group(3)
                year = int(new_match.group(4))
                date = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
                return views, date
        crawler_logger.error(f"Error at: {context}")
        return None

    def _extract_views_and_upload_info(self):
        javascript_query = """
        return document.querySelector("div#bottom-row").querySelector("div#description").querySelector("tp-yt-paper-tooltip").querySelector("#tooltip").textContent
        """
        context = self.driver.execute_script(javascript_query).strip()
        return self.detech_views_and_upload_info(context)

    def run(
        self,
        video_url,
    ):
        try:
            self.driver.get(video_url)
            time.sleep(5)
            self.scroll_down_action(30)
            video_info = self.extract_video_info()
            comments = self.extract_comments()
            data = {
                "video_info": video_info,
                "comments": comments,
            }
            return data
        except Exception as e:
            crawler_logger.error(str(e))


class HomePageCrawler:
    def __init__(self, driver):
        self.driver = driver

    def export_relate_video_info_to_json(self):
        self.save_to_json(
            self.get_all_relate_video_info(), HOME_PAGE_RELATE_VIDEO_INFO_PATH
        )

    def get_all_relate_video_info(self):
        self.driver.get(YOUTUBE_HOMEPAGE_URL)
        time.sleep(5)
        for _ in range(2):
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(3)

        video_info_list = []
        video_thumbnails = self.driver.find_elements(
            "css selector", "a#video-title-link"
        )

        for thumbnail in video_thumbnails:
            video_info = {
                "link": thumbnail.get_attribute("href"),
                "title": thumbnail.get_attribute("title"),
            }
            video_info_list.append(video_info)
        return video_info_list

    def save_to_json(self, data, filename):
        with open(filename, "w") as json_file:
            json.dump(data, json_file, indent=4)


class YoutubeCrawlerTool:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_experimental_option("detach", False)
        options.add_argument("--log-level=3")
        options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)
        self.detail_crawler = DetailCrawler(self.driver)
        self.homepage_crawler = HomePageCrawler(self.driver)

    def run_script1(self):
        """
        Lấy lượng lớn video link ở homepage  => Crawl dữ liệu của từng Video
        """
        # Homepage Process
        list_video_info = self.homepage_crawler.get_all_relate_video_info()
        self.homepage_crawler.save_to_json(
            list_video_info, HOME_PAGE_RELATE_VIDEO_INFO_PATH
        )

        # Video detail Process
        detail_list = []
        for video_info in list_video_info:
            detail_list.append(self.detail_crawler.run(video_info["link"]))

        self._export_to_json(detail_list)
        self.driver.quit()

    @timing_decorator
    def run_script2(self, keyword_list=[]):
        """
        Tìm theo keyword=> Chọn tag Recently Update => Lấy lượng lớn Video link ở màn đó
        => Crawl dữ liệu của từng Video
        """
        total_video = 0
        detail_list = []
        for keyword in keyword_list:
            video_links = self._get_videos_links_by_keyword(keyword)
            total_video += len(video_links)

            crawler_logger.info( #CHECKPOINT 1
                    f"Total video: {total_video}"
            )
            
            try:
                detail_list.append(self.script2_scrape_video(video_links, keyword))
            except Exception as e:
                crawler_logger.error((str(e)))

        result = {"total_video": total_video, "youtube_data": detail_list}
        crawler_logger.info(f"Total Video: {total_video}")
        self._export_to_json(result)
        self.driver.quit()

    def script2_scrape_video(self, video_links, keyword):
        data_by_keyword_dict = {keyword: []}
        for index, video_link in enumerate(video_links):
            try:
                data_by_keyword_dict[keyword].append(
                    self.detail_crawler.run(video_link)
                )
                crawler_logger.info(
                    f"Processing keyword: {keyword} ({index + 1}/{len(video_links)})"
                )
            except Exception as e:
                crawler_logger.error(str(e))
        return data_by_keyword_dict

    def script3_scrape_video(self, video_links, channel_url):
        data_by_keyword_dict = {channel_url: []}
        for index, video_link in enumerate(video_links):
            try:
                data_by_keyword_dict[channel_url].append(
                    self.detail_crawler.run(video_link)
                )
                crawler_logger.info(
                    f"Processing keyword: {channel_url} ({index + 1}/{len(video_links)})"
                )
            except Exception as e:
                crawler_logger.error(str(e))
        return data_by_keyword_dict
    
    def _get_videos_links_by_keyword(self, keyword):
        search_url = f"https://www.youtube.com/results?search_query={keyword}"
        self.driver.get(search_url)

        try:
            # Recently Update Click
            filter_xpath = '//*[@id="chips"]/yt-chip-cloud-chip-renderer[6]'
            video_filter = self.driver.find_element(By.XPATH, filter_xpath)
            video_filter.click()
            time.sleep(3)
            self.detail_crawler.scroll_down_action(100)
            video_links_xpath = (
                '//a[contains(@href, "/watch?v=") and not(contains(@href, "shorts"))]'
            )
            video_links_info = self.driver.find_elements(By.XPATH, video_links_xpath)
            video_links = [link.get_attribute("href") for link in video_links_info]
            return video_links
        except Exception as e:
            crawler_logger.error(str(e))
            return []

    def _get_videos_links_by_channel_url(self, channel_url):
        self.driver.get(channel_url)
        time.sleep(3)
        filter_xpath = '//*[@id="tabsContent"]/tp-yt-paper-tab[2]'
        video_filter = self.driver.find_element(By.XPATH, filter_xpath)
        video_filter.click()
        self.detail_crawler.scroll_down_action(50)
        time.sleep(3)
        video_links_xpath = (
            '//a[contains(@href, "/watch?v=") and not(contains(@href, "shorts"))]'
        )
        video_links_info = self.driver.find_elements(By.XPATH, video_links_xpath)
        video_links = [link.get_attribute("href") for link in video_links_info]
        return video_links
    
    def _export_to_json(self, detail_list):
        detail_json_string = json.dumps(detail_list, indent=4)
        with open(JSON_PATH, "w", encoding="utf-8") as json_file:
            json_file.write(detail_json_string)

    def run_script3(self, channel_url_list=[]):
        """
        Crawl video của từng channel
        Input: List chứa các Channel 
        """
        total_video = 0
        detail_list = []
        for channel_url in channel_url_list:
            video_links = self._get_videos_links_by_channel_url(channel_url)
            total_video += len(video_links)

            crawler_logger.info( 
                    f"Total video: {total_video}"
            )
            try:
                detail_list.append(self.script3_scrape_video(video_links, channel_url))
            except Exception as e:
                crawler_logger.error((str(e)))

        result = {"total_video": total_video, "youtube_data": detail_list}
        crawler_logger.info(f"Total Video: {total_video}")
        self._export_to_json(result)
        self.driver.quit()

if __name__ == "__main__":
    tool = YoutubeCrawlerTool()
    # tool.run_script1()
    # tool.run_script2([
    #     "Amee",
    #     "Amme", "Bray", "Goku", "Liu Grace"
    #     "Andree", "MCK"
    # ])
    tool.run_script3([
        "https://www.youtube.com/channel/UCe8b9jSSD-bNabF4hkNN5PQ",
        "https://www.youtube.com/@Sontungmtp",
        "https://www.youtube.com/@VieTalents"
    ])
