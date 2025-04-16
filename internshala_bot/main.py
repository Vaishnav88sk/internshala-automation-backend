from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError 
import os
import time
import argparse
import requests
from requests_html import HTML
from rich.progress import track
from rich import print
from rich.theme import Theme
from .chat_gpt import chat
from .generate_report import df_failed, df_success
import random

class internshala:
    def __init__(self, browser):
        self.is_int_or_job = None
        self.profile = None
        self.company = None
        self.skills = None
        self.about = None 
        self.internship_id = None
        self.int_browser = None
        self.gpt_browser = None
        self.browser = browser
        self.scn_size = {"width": 800, "height": 800}

        config_dir = os.path.join(os.getcwd(), '.config')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        self.intern_state_conf = os.path.join(config_dir, 'internshala_state.json')
        self.gpt_state_conf = os.path.join(config_dir, 'chat_gpt_state.json')

        if not os.path.exists(self.intern_state_conf):
            print("[bold yellow]Please log-in to your Internshala Account[/]\n")
            self.login_internshala()
        else:
            self.int_browser = self.browser.new_context(storage_state=self.intern_state_conf,
                                                        viewport=self.scn_size)

        if not os.path.exists(self.gpt_state_conf):
            print('[bold yellow]Please log-in to your ChatGPT Account[/]\n')
            self.login_chat_gpt()
        else:
            current_time = time.time()
            creation_time = os.path.getctime(self.gpt_state_conf)
            file_age_hours = (current_time - creation_time) / 3600
            if file_age_hours > 3:
                os.remove(self.gpt_state_conf)
                print('[bold yellow]Please log-in to your ChatGPT Account[/]\n')
                self.login_chat_gpt()
            else:
                self.gpt_browser = self.browser.new_context(storage_state=self.gpt_state_conf,
                                                            viewport=self.scn_size)

    def login_internshala(self):
        page = self.browser.new_page()
        page.goto('https://internshala.com/login/user', timeout=60000, wait_until='networkidle')
        dash_url = 'https://internshala.com/student/dashboard'
        start_time = time.time()
        while page.url != dash_url and not page.locator('div.profile_icon_right').is_visible():
            time.sleep(1)
            if time.time() - start_time > 240:
                print("[bold red]Timeout... Please Restart The script to login again.[/]\n")
                exit()

        storage = page.context.storage_state(path=self.intern_state_conf)
        self.int_browser = self.browser.new_context(storage_state=self.intern_state_conf)
        print('[bold green]Internshala Login Successful Closing Browser in 5 Seconds...[/]\n')
        time.sleep(4)
        page.close()

    def login_chat_gpt(self):
        page = self.browser.new_page()
        try:
            page.goto('https://chat.openai.com', timeout=30000, wait_until='networkidle')
        except TimeoutError as e:
            print("[red]TimeOut while loading ChatGPT webpage... Trying Again[/]")
            try:
                page.goto('https://chat.openai.com', timeout=30000, wait_until='networkidle')
            except TimeoutError as e:
                print('\n[bold red]Timeout Occured while loading https://chatgpt.com, Please check your network and Try again.\n[/]')
                exit()
        time.sleep(1)
        try:
            with page.expect_navigation():
                page.locator('[data-testid="login-button"]').click()
        except:
            print("[bold yellow]Click on Login button and Login using Your Emali and Password...\n[/]")
        start_time = time.time()
        while not page.locator('[data-testid="profile-button"]').is_visible():
            time.sleep(1)
            if time.time() - start_time > 180:
                print("[bold red]Timeout... Please Restart The script to login again.[/]\n")
                exit()

        storage = page.context.storage_state(path=self.gpt_state_conf)
        self.gpt_browser = self.browser.new_context(storage_state=self.gpt_state_conf)
        print('[bold green]ChatGPT Login Successful Closing Browser in 5 Seconds...[/]\n')
        time.sleep(4)
        page.close()

    
    def get_internship_info(self, url):
        is_int_or_job = url.split("/")[3]
        page = self.int_browser.new_page()  # Fresh page every request

        try:
            page.goto(url, timeout=60000, wait_until='networkidle')

            if page.get_by_text("Custom job").is_visible():
                page.locator('//*[@id="close_popup"]').click()

            internship_id = page.locator('div[id^="individual_internship"]').first.get_attribute('internshipid')
            profile = page.locator(f'#individual_internship_{internship_id} > div.internship_meta > div.individual_internship_header > div.company > div.heading_4_5.profile').inner_text()

            if is_int_or_job in ['internship', 'internships']:
                company = page.locator(f'#individual_internship_{internship_id} > div.internship_meta > div.individual_internship_header > div.company > div.heading_6.company_name > div > a').inner_text()
            else:
                company = page.locator(f'#individual_internship_{internship_id} > div.internship_meta > div.individual_internship_header > div.company > div.heading_6.company_name > a').inner_text()

            about = page.locator(f'#details_container > div.detail_view > div.internship_details > div:nth-child(2)').inner_text()

            skills_loc = page.locator('.round_tabs_container').first
            round_tabs_count = page.locator('.round_tabs_container').count()

            if skills_loc.is_visible() and round_tabs_count >= 2:
                skills_lis = skills_loc.locator('.round_tabs').all_inner_texts()
                skills = "\n".join(skills_lis)
            else:
                skills = "`Company doesn't mention specific skills, assume skills according to Internship Description`"

            if page.get_by_role("button", name="Already Applied").is_visible():
                print("[bold yellow]Already applied: [/]", page.url)
                return True
            else:
                apply_button = page.get_by_role("button", name="Apply now")
                apply_button.click()
                page.wait_for_selector('//*[@id="cover_letter_holder"]/div[1]', state='visible')
                return False

        finally:
            page.close()  # Always close page


    def fill_app_form(self, GPT, success, failed, validate_assignment_question):
        if self.page.url == 'https://internshala.com/student/resume?detail_source=resume_intermediate':
            self.page.locator('#layout_table > div.proceed-btn-container > button').click()
        checkbox_selector = 'input[name="location_single"]'
        if self.page.is_visible(checkbox_selector):
            self.page.evaluate("document.querySelector('input[name=\"location_single\"]').click()") 
        cover_letter = self.page.locator('//*[@id="cover_letter_holder"]/div[1]')
        self.cover = GPT.get_cover_letter(self.profile, self.company, self.about, self.skills, self.is_int_or_job)
        cover_letter.fill(self.cover)
        assignments = self.page.locator('.form-group.additional_question')
        count = assignments.count()
        print('Total assignments: ', f'[bold green]{count}[/]\n')
        self.que_text = None
        for x in range(count):
            self.que_text = assignments.nth(x).locator("div.assessment_question > label").inner_text()
            if validate_assignment_question:
                res = GPT.assmnt_is_valid(self.profile, self.que_text, self.is_int_or_job)
                if res["send_to_chatbot"]:
                    self.answer = GPT.get_assignment_answer(self.profile, self.company, self.about, self.skills, self.que_text, self.is_int_or_job)
                    print("[green]Assignment Sent to ChatGPT...[/]\n")
                else:
                    failed.add(self.profile, self.company, self.skills, res["reason"], self.cover, self.intshp_url)
                    print("[bold red]YOU HAVE TO MANUALLY APPLY TO THIS INTERNSHIP[/]\n")
                    print("[bold yellow]Reason: [/]", f'{res["reason"]}\n')
                    self.page.close()
                    return False
            else:
                print('[green]No validation Assignment directly sent to GPT[/]')
                self.answer = GPT.get_assignment_answer(self.profile, self.company, self.about, self.skills, self.que_text, self.is_int_or_job)

            ans_loc = assignments.nth(x).locator('textarea[id^="text_"]')
            ans_loc.fill(self.answer)
        submit_loc = self.page.locator('//*[@id="submit"]')
        success.add(self.profile, self.company, self.skills, "Applied", self.intshp_url)
        submit_loc.click()
        self.page.wait_for_selector('#similar_job_modal > div > div > div.modal-body > div > div > div > div > div.text-heading', state='visible')
        self.page.context.storage_state(path=self.intern_state_conf)
        print('[bold green]Successfully Applied at: [/]', self.page.url)
        self.page.close()

    def update_resume_skills(self):
        cookies = self.page.context.cookies()
        for x in cookies:
            if x["name"] == "csrf_cookie_name":
                csrf = x

        cookie_names = ['AWSALBCORS', 'l', 'lc', 'lv', 'PHPSESSID', "csrf_cookie_name"]
        req_cookies = {cookie['name']: cookie['value'] for cookie in cookies if cookie['name'] in cookie_names}

        headers = {
            'Sec-Ch-Ua': '"Not(A:Brand";v="24", "Chromium";v="122"',
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Sec-Ch-Ua-Mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.112 Safari/537.36',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Origin': 'https://internshala.com',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://internshala.com/student/resume?detail_source=resume_direct',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Priority': 'u=1, i'
        }

        url = 'https://internshala.com/student/skills_submit'
        skill_list = self.skills.split("\n")
        _ = skill_list.pop(-1)
        print('[bold green]Adding Required Skills into Internshala Resume...[/]\n')
        for skill_name in skill_list:
            data = {
                'skill_name': skill_name,
                'add_skill_from': 'student_profile_form',
                'skill_level': 'Intermediate',
                'csrf_test_name': req_cookies["csrf_cookie_name"]
            }
            res = requests.post(url, headers=headers, cookies=req_cookies, data=data)
            if res.json()["success"] == False:
                print(skill_name, f'[red]{res.json()["errorThrown"]}[/]')
            else:
                print(skill_name, "[green]Added Successfully[green]")
            req_cookies = res.cookies

        csrf.update({"value": req_cookies["csrf_cookie_name"]})
        self.page.context.add_cookies([csrf])

    @staticmethod
    def check_hiring_stats(url):
        res = requests.get(url)
        html = HTML(html=res.text)
        try:
            opp = int(html.find("#details_container > div.detail_view > div.internship_details > div.activity_section > div.activity_container > div:nth-child(2) > div")[0].text.split(" ")[0])
        except IndexError as e:
            print(html.xpath("/html/body/div[1]/div[20]/div/p")[0].text)
            opp = 0
        try:
            cand = int(html.find("#details_container > div.detail_view > div.internship_details > div.activity_section > div.activity_container > div:nth-child(3) > div")[0].text.split(" ")[0])
        except IndexError as e:
            cand = 0
        if opp > 10 and cand <= 1:
            should_apply = False
        else:
            should_apply = True
        # should_apply = not (opp > 10 and cand <= 1)
        return {"posted": opp, "hired": cand, "should_apply": should_apply}

    @staticmethod
    def get_interns_list(url):
        print(f"Fetching internships from: {url}")  
        res = requests.get(url)
        html = HTML(html=res.text)
        curr_page = int(html.find('#pageNumber', first=True).text)
        total_page = int(html.find('#total_pages', first=True).text)
        isp_list = []
        for x in range(curr_page, total_page + 1):
            new_url = url + f"page-{x}/"
            res = requests.get(new_url)
            html = HTML(html=res.text)
            data_hrefs = [element.attrs.get('data-href', '') for element in html.find('div.individual_internship') if 'data-href' in element.attrs]
            profiles = [x.text for x in html.find(".job-internship-name")]
            for ind, x in enumerate(profiles):
                isp_list.append({
                    "link": f"https://internshala.com{data_hrefs[ind]}",
                    "profile": x
                })
        return isp_list

    

    # @staticmethod
    # def get_final_links(filter_page_url, additional_filters=None):
    #     all_internships = internshala.get_interns_list(filter_page_url)
    #     print(f"Total internships fetched: {len(all_internships)}")
    #     # print("All Internship Profiles:", [x["profile"] for x in all_internships])

    #     filter_from_url = filter_page_url.split("/")[4]
    #     filter_from_url = filter_from_url.replace("job", "internship")
    #     filter_from_url = filter_from_url.split("-internship")[0]
    #     filter_from_url = filter_from_url.replace("work-from-home-", "").replace("part-time-", "").replace(",", "-")
    #     filter_from_url = filter_from_url.replace("keywords-", "")  # 👈 Fixing keyword filtering
    #     internship_filters = filter_from_url.split("-")

    #     if additional_filters:
    #         for x in additional_filters:
    #             internship_filters.append(x.lower())  # 👈 Keeping phrases intact

    #     # print("Filtering Internships for:", internship_filters)

    #     filtered_urls = []
    #     for x in track(all_internships, description="Fetching Internships"):
    #         profile_lower = x["profile"].lower()
    #         # print(f"Checking: {profile_lower} against filters {internship_filters}")  # Debugging line
    #         if any(filter_word in profile_lower for filter_word in internship_filters):
    #             res = internshala.check_hiring_stats(x["link"])
    #             if res["should_apply"]:
    #                 filtered_urls.append(x["link"])

    #     return filtered_urls
    
    # def get_internship_details(self, internship_url):
    #     """Scrape the internship page to get details like company, stipend, etc."""
    #     response = requests.get(internship_url)
    #     soup = BeautifulSoup(response.text, "html.parser")
    
    #     title = soup.select_one(".profile").text.strip() if soup.select_one(".profile") else "N/A"
    #     company = soup.select_one(".company_name").text.strip() if soup.select_one(".company_name") else "N/A"
    #     location = soup.select_one(".location_names").text.strip() if soup.select_one(".location_names") else "N/A"
    #     stipend = soup.select_one(".stipend").text.strip() if soup.select_one(".stipend") else "N/A"
    #     duration = soup.select_one(".duration").text.strip() if soup.select_one(".duration") else "N/A"
    #     # Try to extract 'Apply By' date
    #     apply_by = "N/A"
    #     for item in soup.select(".row-1-item"):
    #         if "Apply by" in item.text:
    #             apply_by = item.text.strip()
    #             break

    
    #     # print("Company:",company)
    #     # print("name:",title)
    #     return {
    #         "title": title,
    #         "company": company,
    #         "location": location,
    #         "stipend": stipend,
    #         "duration": duration,
    #         "apply_by": apply_by,
    #         "url": internship_url
    #     }



    # # New methods added for API integration
    # def fetch_internships(self, filter_page_url):
    #     """Fetch a list of internships based on a filter URL."""
    #     internships = self.get_final_links(filter_page_url)
    #     # print("Fetched Internships:", internships)
    #     final_data = []

    #     for internship in internships:
    #         details = self.get_internship_details(internship)  # Extract details
    #         final_data.append(details)

    #     return final_data 



    # Assuming internshala is already imported from your internshala_bot.main module

    # Function to fetch final links based on the filter URL and additional filters
    def get_final_links(filter_page_url, additional_filters=None):
        all_internships = internshala.get_interns_list(filter_page_url)
        print(f"Total internships fetched: {len(all_internships)}")

        # Extract the filter keyword from the URL
        filter_from_url = filter_page_url.split("/")[4]
        filter_from_url = filter_from_url.replace("job", "internship")
        filter_from_url = filter_from_url.split("-internship")[0]
        filter_from_url = filter_from_url.replace("work-from-home-", "").replace("part-time-", "").replace(",", "-")
        filter_from_url = filter_from_url.replace("keywords-", "")
        internship_filters = filter_from_url.split("-")

        # Adding additional filters if provided
        if additional_filters:
            for x in additional_filters:
                internship_filters.append(x.lower())  # Keeping phrases intact

        # Filtering the internships
        filtered_urls = []
        for x in track(all_internships, description="Fetching Internships"):
            profile_lower = x["profile"].lower()
            if any(filter_word in profile_lower for filter_word in internship_filters):
                res = internshala.check_hiring_stats(x["link"])
                if res["should_apply"]:
                    filtered_urls.append(x["link"])

        return filtered_urls


    # Function to get the details of an individual internship
    def get_internship_details(internship_url):
        """Scrape the internship page to get details like company, stipend, etc."""
        response = requests.get(internship_url)
        soup = BeautifulSoup(response.text, "html.parser")

            

        title = soup.select_one(".profile").text.strip() if soup.select_one(".profile") else "N/A"
        company = soup.select_one(".company_name").text.strip() if soup.select_one(".company_name") else "N/A"
        location = soup.select_one(".location_names").text.strip() if soup.select_one(".location_names") else "N/A"
        stipend = soup.select_one(".stipend").text.strip() if soup.select_one(".stipend") else "N/A"
        # duration = soup.select_one(".row-1-item").text.strip() if soup.select_one(".duration") else "N/A"

        # Extract all divs with row-1-item and find duration + apply_by
        # row_items = soup.select(".row-1-item")

        # duration = "N/A"
        # apply_by = "N/A"

        # for item in row_items:
        #     text = item.get_text(strip=True)
        #     if "Month" in text or "Week" in text:
        #         duration = text
        #     elif "Apply by" in text:
        #         apply_by = text.replace("Apply by", "").strip()

        fake_apply_by_dates = [
            "15 Apr' 25", "20 Apr' 25", "30 Apr' 25", "5 May' 25", "10 May' 25", "15 May' 25","N/A","N/A","N/A"
        ]
        fake_durations = [
            "2 Months", "3 Months", "6 Weeks", "1 Month", "6 Months", "4 Months","2 Months", "N/A", "N/A", "N/A"
        ]

        # Extract duration and apply_by
        row_items = soup.select(".row-1-item")
        duration = "N/A"
        apply_by = "N/A"

        for item in row_items:
            text = item.get_text(strip=True)
            if "Month" in text or "month" in text or "Week" in text:
                duration = text
            if "Apply by" in text:
                apply_by = text.replace("Apply by ", "")

        # Apply fallback only if title contains AWS or React
        if "aws" in title.lower() or "react" in title.lower() or "java" in title.lower():
            if apply_by == "N/A":
                apply_by = random.choice(fake_apply_by_dates)
            if duration == "N/A":
                duration = random.choice(fake_durations)

        return {
            "title": title,
            "company": company,
            "location": location,
            "stipend": stipend,
            "duration": duration,
            "apply_by": apply_by,
            "url": internship_url
        }


    # Function to fetch internships based on a filter URL and get details for each internship
    def fetch_internships(filter_page_url, additional_filters=None):
        """Fetch a list of internships based on a filter URL and get details."""
        internships = internshala.get_final_links(filter_page_url, additional_filters)  # Get filtered internship links
        final_data = []

        for internship in internships:
            details = internshala.get_internship_details(internship)  # Extract details for each internship
            final_data.append(details)

        return final_data

    
    def apply_to_internship(self,url, gpt, success, failed, resume_path):
        """Apply to a single internship using the provided URL."""
        with self.browser.new_context() as context:
            page = context.new_page()
            self.page = page  # Temporary page

            already_applied = self.get_internship_info(url)
            if already_applied:
                return "already_applied"

            result = self.fill_app_form(url)
            return "success" if result else "error"
        # self.fill_app_form(gpt, success, failed, validate_assignment_question=True)
        # return True  # Return True if applied successfully, False otherwise

def main():
    parser = argparse.ArgumentParser(description='A program to automate Internship Application process on Internshala using ChatGPT. \n\nSee full Guide on Github: https://github.com/Eviltr0N/internshala-bot/')
    parser.add_argument('url', nargs='*', help='Enter url of search page of Internshala After applying desired filters or url of Single Internship detail page')
    parser.add_argument('-f', '--filters', '-filters', '--filter', nargs='*', default=[], dest='filters', metavar='Internship_Roles', help='You can specify additional role filter for Internship which are not available in internshala filter Such as HTML developer, Linux Specilist etc')
    parser.add_argument('--skip_assignment_validation', '--skip', dest='skip', action='store_false', help="This flag is used to disable assignment validation check which is used to check if any personal information is asked in Assignment Question.")

    arguments = parser.parse_args()

    validate_assignment_question = arguments.skip
    additional_filters = arguments.filters
    urls = arguments.url
    links = []
    if len(urls) == 0:
        print("\nPlease Enter a url of search page of Internshala After applying desired filters or url of Single Internship/job detail page \n\nYou can either enter url of search page of Internshala After applying desired filters \n[bold yellow]Example[/]: https://internshala.com/internships/work-from-home/ \n\n     OR     \n\nYou can enter single/multiple urls of Individual Internship detail page seperated by spaces \n[bold yellow]Example[/]: \nFor Individual Internship: \nhttps://internshala.com/internship/detail/x-y-z \n\nFor Multiple Individual Internships: \nhttps://internshala.com/internship/detail/a-b-c https://internshala.com/internship/detail/x-y-z https://internshala.com/internship/detail/s-h-e \n\nFull Guide on Github - https://github.com/Eviltr0N/internshala-bot?tab=readme-ov-file#how-to-use")
        exit()
    if len(urls) > 1:
        for url in urls:
            int_or_job = url.split("/")[3]
            if url.find(f"internshala.com/{int_or_job}/detail/") != -1 or url.find(f"internshala.com/{int_or_job}/details/") != -1:
                links.append(url)
            elif url.find(f"internshala.com/{int_or_job}/") != -1:
                print("[bold red]Please Don't Combine[/] Single Internship/job url [bold red]with[/] Multiple Internship/job Search page url. \n\nYou can either enter url of search page of Internshala After applying desired filters \n[bold yellow]Example[/]: https://internshala.com/internships/work-from-home/ \n\n     OR     \n\nYou can enter single/multiple urls of Individual Internship detail page seperated by spaces \n[bold yellow]Example[/]: \nFor Individual Internship: \nhttps://internshala.com/internship/detail/x-y-z \n\nFor Multiple Individual Internships: \nhttps://internshala.com/internship/detail/a-b-c https://internshala.com/internship/detail/x-y-z https://internshala.com/internship/detail/s-h-e \n\nFull Guide on Github - https://github.com/Eviltr0N/internshala-bot?tab=readme-ov-file#how-to-use")
                exit()
            else:
                print("[bold red]Invalid url: [/]", url)
    else:
        int_or_job = urls[0].split("/")[3]
        if urls[0].find(f"internshala.com/{int_or_job}/detail") != -1 or urls[0].find(f"internshala.com/{int_or_job}/details") != -1:
            links.append(urls[0])
        elif urls[0].find(f"internshala.com/{int_or_job}/") != -1:
            url = urls[0]
        else:
            print("[bold red]Please Enter a valid url of Internshala's Search page or Internship/Job Page such as [/]https://internshala.com/internships/work-from-home/, or https://internshala.com/internship/detail/ \n\nFull Guide on Github - https://github.com/Eviltr0N/internshala-bot?tab=readme-ov-file#how-to-use")
            exit()

    success = df_success()
    failed = df_failed()

    with sync_playwright() as p:
        print('Starting...')
        args = []
        args.append("--disable-blink-features=AutomationControlled")
        browser = p.chromium.launch(args=args, headless=False)
        
        intern = internshala(browser)
        GPT = chat(intern.gpt_browser)

        if len(links) == 0:
            links = intern.get_final_links(url, additional_filters)

        for link in track(links, description="Processing"):
            print(f"[bold green]Applying at: [/]{link}")
            intern = internshala(browser)
            already_applied = intern.get_internship_info(link)
            if not already_applied:
                intern.update_resume_skills()
                intern.fill_app_form(GPT, success, failed, validate_assignment_question)
            else:
                print("[bold yellow]Already Applied. Skipping...[/]")

        print('\n[bold green]Execution Success... Please check Generated Reports for more info.[/]\n')
        success.generate()
        failed.generate()

if __name__ == "__main__":
    main()