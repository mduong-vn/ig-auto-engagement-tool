from multiprocessing.connection import wait
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException, StaleElementReferenceException
from tkinter import messagebox
import tkinter as tk
import time
import os
import pickle 
import builtins
import ctypes
import threading
import sys
import random

stop_event = threading.Event()

def random_delay(min_delay=1, max_delay=3):
    time.sleep(random.uniform(min_delay, max_delay))

def random_mouse_movement(driver):
    try:
        body = driver.find_element(By.TAG_NAME, 'body')
        width = body.size['width']
        height = body.size['height']
        for _ in range(random.randint(5, 15)):
            x_offset = random.randint(0, width)
            y_offset = random.randint(0, height)
            ActionChains(driver).move_to_element_with_offset(body, x_offset, y_offset).perform()
            time.sleep(random.uniform(0.1, 0.3))
    except Exception:
        pass

# redirect print to logger
def set_logger(log_func):
    original_print = builtins.print
    def custom_print(*args, **kwargs):
        message = " ".join(str(a) for a in args)
        try:
            log_func(message)
        except Exception:
            pass
        original_print(*args, **kwargs)
    builtins.print = custom_print

# setup driver
def setup_driver():
    try:
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7339.208 Safari/537.36"
        )        
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--metrics-recording-only")
        options.add_argument("--mute-audio")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--lang=en-US")
        options.add_experimental_option("prefs", {"credentials_enable_service": False, "profile.password_manager_enabled": False})
        driver_path = os.path.join(os.path.dirname(__file__), "chromedriver.exe")
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        return driver
    except Exception as e:
        print(f"💩 error setting up driver: {e}")
        return None

# save 🍪
def save_cookies(driver, user):
    cookie_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{user}_cookies.pkl")
    cookies = driver.get_cookies()
    with open(cookie_file, 'wb') as file:
        pickle.dump(cookies, file)
    print(f"🍪 saved to {cookie_file}")

# load 🍪
def load_cookies(driver, user):
    cookie_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{user}_cookies.pkl")
    if not os.path.exists(cookie_file):
        return False
    try:
        driver.get("https://www.instagram.com")
        time.sleep(2)
        with open(cookie_file, 'rb') as file:
            cookies = pickle.load(file)
        if not isinstance(cookies, list) or not cookies:
            return False
        loaded_any = False
        for cookie in cookies:
            try:
                cookie.pop('sameSite', None)
                if 'expiry' in cookie:
                    cookie['expiry'] = int(cookie['expiry'])
                driver.add_cookie(cookie)
                loaded_any = True
            except Exception as e:
                pass
        if not loaded_any:
            return False
        
        # refresh to apply cookies
        driver.get("https://www.instagram.com")
        time.sleep(4)
        if driver.current_url != "https://www.instagram.com/":
            return False
        return True
    except Exception as e:
        return False

# login
def login(driver, user, pwd):
    driver.get("https://www.instagram.com/")
    random_mouse_movement(driver)
    try:
        user_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        pwd_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        random_mouse_movement(driver)
        user_field.clear()
        pwd_field.clear()
        user_field.send_keys(user)
        pwd_field.send_keys(pwd)
        pwd_field.submit()
        time.sleep(5)
        random_mouse_movement(driver)

        # check if login successful
        random_delay(8,10)
        current_url = driver.current_url
        valid_urls = ["https://www.instagram.com/", "https://www.instagram.com/accounts/onetap/?next=%2F", "https://www.instagram.com/accounts/onetap/"]
        if current_url not in valid_urls:
            if load_cookies(driver, user):
                return True
            else:
                raise Exception("login failed, check credentials")
            
        # save cookies
        save_cookies(driver, user)
        return True
    except Exception as e:
        return False

# report
def report(driver, report):
    report = report.strip()
    if not report.startswith("http") or not report.startswith("instagram.com"):
        url = "https://www.instagram.com/" + report.lstrip("/")
    else:
        url = report
    try:
        driver.get(url)
        random_delay(3,4)
        random_mouse_movement(driver)
        if "Sorry, this page isn't available." in driver.page_source:
            print(f"💩 account defeated")
            return True
        
        # click 3 dots
        three_dots = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH, "//*[name()='svg'][@aria-label='Options']/.."
                )
            )
        )
        three_dots.click()

        # click report
        report_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH, "//button[contains(text(),'Report')]"
                )
            )
        )
        report_button.click()

        # select reason (spam)
        report_acc = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH, "//button[.//div/div[text()='Report Account']]"
                )
            )
        )
        random_mouse_movement(driver)
        report_acc.click()

        # select reason 1
        report_reason_1 = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH, "//button[.//div[contains(text(),\"It's posting content that shouldn't be on Instagram\")]]"
                )
            )
        )
        report_reason_1.click()

        # select reason 2
        report_reason_2 = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH, "//button[.//div/div[text()='Violence, hate or exploitation']]"
                )
            )
        )
        report_reason_2.click()

        # select reason 3
        report_reason_3 = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH, "//button[.//div/div[text()='Hate speech or symbols']]"
                )
            )
        )
        report_reason_3.click()

        # confirm
        complete_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH, "//button[contains(text(),'Close')]"
                )
            )
        )
        random_mouse_movement(driver)
        complete_button.click()
        random_delay(2,3)
        print(f"💜 reported {report}")
        return True
    except Exception as e:
        print(f"💩 error reporting {report}: {e}")
        return False

class AccountRestrictedError(Exception):
    pass

# like and comment
def like_comment(driver, profile, comments, num_posts, user, links=None):
    random_delay()
    try:
        if not links:
            if "instagram.com" in profile:
                driver.get(profile)
            else:
                driver.get("https://www.instagram.com/" + profile)
            random_delay(3,5)
            random_mouse_movement(driver)
            
            # get posts
            for _ in range(5):
                driver.execute_script("window.scrollBy(0, 500);")
                random_delay(1, 2)
            random_delay(3,5)

            elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (
                        By.XPATH, "//a[contains(@href, '/p/') or contains(@href, '/reel/')]"
                    )
                )
            )
            hrefs = []
            for el in elements:
                try:
                    href = el.get_attribute("href")
                    if href:
                        hrefs.append(href)
                except Exception:
                    continue
            posts = hrefs[:max(1, int(num_posts))]
        else:
            posts = []
            for link in links:
                if not link:
                    continue
                s=link.strip()
                posts.append(s)

        local_comments=comments.copy() if isinstance(comments, list) else [comments]
        for i,link in enumerate(posts):
            if stop_event.is_set():
                break
            try:
                driver.get(link)
                random_delay(4,6)
                random_mouse_movement(driver)
                actions = ActionChains(driver)

                # like post
                like_button =  WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//section[.//*[name()='svg'][@aria-label='Comment' or @aria-label='Share']and not(.//main[@class])]//*[name()='svg'][@aria-label='Like' or @aria-label='Unlike']/ancestor::*[@role='button']")
                    )
                )

                # check if already liked
                aria_label = like_button.find_element(By.XPATH, ".//*[name()='svg']").get_attribute("aria-label")

                profile_name = profile if profile else "media"

                if aria_label == "Like":
                    driver.execute_script("arguments[0].click();", like_button)
                    try:
                        restrict_popup = WebDriverWait(driver, 2).until(
                            EC.presence_of_element_located(
                                (By.XPATH, "//div[@role='dialog'][.//text()[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'restrict')]]")
                            )
                        )
                        if restrict_popup:
                            raise AccountRestrictedError(f"💩 ur account {user} is restricted lmao")
                            
                    except TimeoutException:
                        print(f"liked post {i+1} of {profile_name}")

                elif aria_label == "Unlike":
                    print(f"already liked post {i+1} of {profile_name}")
                else:
                    print(f"💩 can't find like button in post {i+1} of {profile_name}")
                random_delay(2,4)

                # save post
                save_button =  WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//section[.//*[name()='svg'][@aria-label='Comment' or @aria-label='Share']and not(.//main[@class])]//*[name()='svg'][@aria-label='Save' or @aria-label='Remove']/ancestor::*[@role='button']")
                    )
                )

                # check if already saved
                aria_label = save_button.find_element(By.XPATH, ".//*[name()='svg']").get_attribute("aria-label")
                if aria_label == "Save":
                    actions.move_to_element(save_button).click().perform()
                    random_delay(1,2)
                    print(f"saved post {i+1} of {profile_name}")
                elif aria_label == "Remove":
                    print(f"already saved post {i+1} of {profile_name}")
                else:
                    print(f"💩 can't find save button in post {i+1} of {profile_name}")

                # comment
                if local_comments:
                    try:
                        comment_area = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable(
                                (
                                    By.XPATH, "//textarea[@aria-label='Add a comment…']"
                                )
                            )
                        )
                        comment = random.choice(local_comments)
                        local_comments.remove(comment)
                        
                        actions.move_to_element(comment_area).click().send_keys(comment).send_keys(Keys.ENTER).perform()
                        random_delay(4,6)
                        print(f"commented on post {i+1} of {profile_name}: {comment}")
                    except Exception as e:
                        print(f"💩 comment failed: {e}")
                else:
                    print(f"💩 no comments left, only liked")
                random_delay(2,4)

            except AccountRestrictedError:
                raise
            except Exception as e:
                print(f"💩 error on post {i+1} of {profile_name}: {e}")
                random_delay(2,4)

        return True
    except AccountRestrictedError:
        raise
    except Exception as e:
        print(f"💩 error getting posts of {profile_name}: {e}")
        return False


# post new posts
def post_new(driver, image_paths, tags, caption, hashtags, user):
    
    def strip_non_bmp(text: str) -> str:
        return ''.join(c for c in text if ord(c) <= 0xFFFF)
    
    image_paths = [os.path.abspath(p) for p in image_paths if os.path.exists(p)]
    if not image_paths:
        print("💩 no valid image paths")
        return False
    
    wait = WebDriverWait(driver, 15)
    actions = ActionChains(driver)

    local_captions = caption.copy() if isinstance(caption, list) else [caption]

    for idx, path in enumerate(image_paths):
        is_video = path.lower().endswith((".mp4", ".mov", ".avi", ".mkv"))
        if not os.path.exists(path):
            print(f"💩 image path does not exist: {path}")
            return False
        try:
            driver.get(f"https://www.instagram.com/")
            random_mouse_movement(driver)
            
            # upload media
            try:
                create_btn = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "svg[aria-label='New post']")))
                actions.move_to_element(create_btn).click().perform()
                time.sleep(2)

                upload_input = driver.find_elements(
                    By.XPATH, "//input[@type='file' and (contains(@accept,'image') and contains(@accept,'video'))]"
                )
                if upload_input:
                    upload_input[0].send_keys(image_paths[idx])
                else:
                    post_btn = wait.until( EC.element_to_be_clickable((By.CSS_SELECTOR, "svg[aria-label='Post']")) )
                    actions.move_to_element(post_btn).click().perform()

                    upload_input = wait.until(EC.presence_of_element_located(
                        (By.XPATH, "//input[@type='file' and (contains(@accept,'image') and contains(@accept,'video'))]") 
                    ))
                    upload_input.send_keys(image_paths[idx])

                try:
                    popup_ok = wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "//button[text()='OK']")))
                    popup_ok.click()
                except TimeoutException:
                    pass

            except TimeoutException as e:
                print("💩 can't find upload input:", e)
                return False
            
            random_mouse_movement(driver)
            random_delay(3,5)

            # change to original size
            try:                
                select_crop = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Select crop')]"))
                )
                # hide back button
                back_btn = driver.find_elements(By.XPATH, "//div[@role='button' and contains(., 'Back')]")
                if back_btn:
                    driver.execute_script("arguments[0].style.display='none';", back_btn[0])
                actions.move_to_element(select_crop).click().perform()

                time.sleep(2)
                photo_outline = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and contains(., 'Original')]"))
                )
                actions.move_to_element(photo_outline).click().perform()
            except Exception as e:
                print("💩 can't change to original size:", e)

            # next
            next_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and text()='Next']"))
            )
            driver.execute_script("arguments[0].click();", next_btn)
            random_delay(2,4)
            random_mouse_movement(driver)

            next_btn = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and text()='Next']"))
            )
            driver.execute_script("arguments[0].click();", next_btn)
            random_delay(2,4)
            random_mouse_movement(driver)

            # add caption
            if local_captions:
                caption = random.choice(local_captions)
                local_captions.remove(caption)
            else:
                caption = ""
            caption_area = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@role='textbox' and @aria-label='Write a caption...']")
                )
            )
            caption_area.send_keys(strip_non_bmp(caption) + "\n")
            random_delay(1,2)
            random_mouse_movement(driver)

            # add tags
            for tag in tags:
                caption_area.send_keys(strip_non_bmp(f"@{tag}\n"))

            # default hashtag
            for hashtag in hashtags:
                caption_area.send_keys(strip_non_bmp(f"#{hashtag}\n"))
            random_mouse_movement(driver)

            # tag on img
            try:
                if is_video:
                    count_tag = 0
                    for tag in tags:
                        if count_tag == 0:
                            tag_btn = wait.until( EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Tag people')]")))
                            tag_btn.click()
                        else:
                            add_tag_btn = wait.until( EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Add tag')]")))
                            add_tag_btn.click()
                        user_input = wait.until(
                            EC.presence_of_element_located((By.XPATH, "//input[@name='userSearchInput']"))
                        )
                        user_input.clear()
                        user_input.send_keys(tag)
                        time.sleep(2)
                        random_mouse_movement(driver)
                        xpath = f"//button[.//span[@role='link']/*[@alt=\"{tag}'s profile picture\"]]"

                        first_user = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                        first_user.click()
                        count_tag += 1
                        random_delay(1,2)
                else:
                    SAFE_MARGIN = 20
                    VERTICAL_GAP = 50
                    for i, tag in enumerate(tags):
                        try:
                            photo_img = wait.until(EC.presence_of_element_located(
                                (By.XPATH, "//img[@alt='Photo for tag placement']")
                            ))
                            tag_btn = photo_img.find_element(By.XPATH, "following-sibling::div[@role='button' and not(@style)]")
                            
                            # tag top left
                            offset_x = SAFE_MARGIN
                            offset_y = SAFE_MARGIN + i * VERTICAL_GAP
                            offset_y = min(offset_y, photo_img.size['height'] - SAFE_MARGIN)
                            actions.move_to_element_with_offset(tag_btn, offset_x, offset_y).click().perform()
                            time.sleep(1)
                            
                            # search user
                            user_input = wait.until(
                                EC.presence_of_element_located((By.XPATH, "//input[@name='userSearchInput']"))
                            )
                            user_input.clear()
                            user_input.send_keys(tag)
                            time.sleep(2)
                            random_mouse_movement(driver)
                            xpath = f"//button[.//span[@role='link']/*[@alt=\"{tag}'s profile picture\"]]"

                            first_user = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                            first_user.click()
                    
                        except Exception as e:
                            print(f"💩 can't tag people on image: {e}")

            except Exception as e:
                print(f"💩 error tagging: {e}")
            
            random_delay(2,4)
            # share
            share_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[@role='button' and text()='Share']")
                )
            )
            share_btn.click()
            random_delay(10,15)
            print(f"posted {path} for account {user}")
            return True
        except Exception as e:
            print(f"💩 error posting new content: {e}")
            return False


def safe_showerror(title, message):
    try:
        if tk._default_root is not None:
            tk._default_root.after(0, lambda: messagebox.showerror(title, message))
        else:
            messagebox.showerror(title, message)
    except Exception as e:
        pass