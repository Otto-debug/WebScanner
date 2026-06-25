import time
import random
import string
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select


from utils.logger import logger

import traceback

class ScannerJuiceShopXSS:
    def __init__(self, headless=True):
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        # Путь к chromedriver
        service = Service(executable_path='/usr/bin/chromedriver')
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(15)
        self.base_url = "http://localhost:3000"
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.result = []

    def register_user(self, email, password):
        url = f"{self.base_url}/api/Users"
        data = {
            "email": email,
            "password": password,
            "passwordRepeat": password,
            "securityQuestion": 1,
            "securityAnswer": "test"
        }
        try:
            resp = self.session.post(url, json=data)
            if resp.status_code == 201:
                logger.debug(f"Registered {email}")
                return True
            else:
                logger.error(f"Registration failed: {resp.status_code}")
        except Exception as e:
            logger.error(f"Failed Registration: {e}")
        return False

    def login(self, email, password):
        self.driver.get(f"{self.base_url}/#/login")
        try:
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_field.send_keys(email)
            password_field = self.driver.find_element(By.ID, "password")
            password_field.send_keys(password)
            login_btn = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "loginButton"))
            )
            self.driver.execute_script("arguments[0].click();", login_btn)

            WebDriverWait(self.driver, 15).until(
                lambda d: d.execute_script(
                    "return localStorage.getItem('token')"
                ) is not None
            )

            token = self.driver.execute_script(
                "return localStorage.getItem('token')"
            )

            print(token)

            logger.debug(f"Successful login: {email}")
            return True
        except Exception as e:
            logger.error(f"Login Failed: {e}")
            return False

    def test_search_debug(self):
        self.driver.get(f"{self.base_url}/#/")

        # Закрываем баннеры
        try:
            banner = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[aria-label='Close Welcome Banner']"))
            )
            self.driver.execute_script("arguments[0].click();", banner)
        except:
            pass

        try:
            cookie = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[aria-label='dismiss cookie message']"))
            )
            self.driver.execute_script("arguments[0].click();", cookie)
        except:
            pass

        search_button = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".search-toggle"))
        )

        print("Button: ", search_button.get_attribute("outerHTML"))

        # JS click
        self.driver.execute_script("arguments[0].click();", search_button)
        time.sleep(2)

        search_query = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.ID, "searchQuery"))
        )

        print("\nTag: ", search_query.tag_name)
        print("\nOuter: ", search_query.get_attribute("outerHTML"))

        inputs = self.driver.find_elements(By.TAG_NAME, 'input')

        print("\nInputs: ", len(inputs))

        for i, inp in enumerate(inputs):
            print(f"\nINPUT: #{i}")
            print(inp.get_attribute("outerHTML"))

    def test_search_reflection(self):

        payload = '<img src=x onerror="window.xss_detected=`XSS_Search`">'
        try:
            logger.info(f"Testing search {self.base_url}/#/")
            self.driver.get(f"{self.base_url}/#/")

            time.sleep(3)
            # open search
            search_btn = WebDriverWait(self.driver, 30).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, ".search-toggle")
                )
            )

            print("DISPLAYED:", search_btn.is_displayed())
            print("ENABLED:", search_btn.is_enabled())
            print("CLASS:", search_btn.get_attribute("class"))


            self.driver.execute_script("arguments[0].click();", search_btn)

            # real input
            search_input = WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "app-mat-search-bar input"))
            )

            search_input.clear()
            self.driver.execute_script("""
                    window.xss_detected = null;
                    """)
            search_input.send_keys(payload)
            print(self.driver.current_url)
            print("INPUT VALUE:")
            print(search_input.get_attribute("value"))

            search_input.send_keys(Keys.ENTER)
            print(self.driver.current_url)

            time.sleep(2)

            print(
                self.driver.find_element(
                    By.TAG_NAME,
                    "body"
                ).get_attribute("innerHTML")
            )

            time.sleep(3)

            print(
                self.driver.execute_script(
                    "return window.xss_detected"
                )
            )
            detected = self.driver.execute_script(
                "return window.xss_detected"
            )
            logger.info(f"XSS Detected: {detected}")

            if detected == "XSS_Search":
                logger.warning(f"[XSS] Reflected XSS detected in search: {payload}")
                self.result.append(("Reflected_XSS_Search", "", "", payload))
            else:
                logger.info(f"[XSS] Xss not detected: {payload}")
        except Exception as e:
            logger.error(f"Error XSS in search: {e}")

    def test_xss_review(self):

        payload = 'Nice product <img src=x onerror="window.xss_detected=`XSS_Review`">'

        rand_suffix = ''.join(
            random.choices(string.ascii_lowercase, k=6)
        )

        email = f"xss_test_{rand_suffix}@test.com"
        password = "Password123"

        # Register
        if not self.register_user(email, password):
            logger.error("Регистрация не удалась")
            return

        # Login
        if not self.login(email, password):
            logger.error("Логин не удался")
            return

        # Open main page
        self.driver.get(f"{self.base_url}/#/")

        # Init marker AFTER page load
        self.driver.execute_script("""
            window.xss_detected = null;
        """)

        # Close welcome banner
        try:
            logger.info(f"Testing product {self.base_url}/#/")
            banner = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR,
                     "button[aria-label='Close Welcome Banner']")
                )
            )

            self.driver.execute_script(
                "arguments[0].click();",
                banner
            )

        except:
            pass

        # Close cookie banner
        try:
            cookie = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR,
                     "a[aria-label='dismiss cookie message']")
                )
            )

            self.driver.execute_script(
                "arguments[0].click();",
                cookie
            )

        except:
            pass

        # Wait product image
        product = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".mat-card img")
            )
        )

        # Open product dialog
        self.driver.execute_script(
            "arguments[0].click();",
            product
        )

        # Wait dialog appear
        WebDriverWait(self.driver, 20).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "mat-dialog-container")
            )
        )

        # Wait textarea
        textarea = WebDriverWait(self.driver, 20).until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, "mat-dialog-container textarea")
            )
        )
        time.sleep(1)
        textarea.click()

        textarea.clear()

        textarea.send_keys(payload)

        # DEBUG
        logger.debug(
            f"Textarea value: {textarea.get_attribute('value')}"
        )

        # Wait submit button
        submit_btn = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located(
                (By.ID, "submitButton")
            )
        )

        print("TEXTAREA VALUE:")
        print(textarea.get_attribute("value"))

        print("SUBMIT ENABLED:")
        print(submit_btn.is_enabled())

        print("SUBMIT DISABLED ATTR:")
        print(submit_btn.get_attribute("disabled"))

        print("SUBMIT CLASS:")
        print(submit_btn.get_attribute("class"))

        # Wait button enabled
        WebDriverWait(self.driver, 10).until(
            lambda d: submit_btn.is_enabled()
        )

        logger.debug(
            f"Submit enabled: {submit_btn.is_enabled()}"
        )

        # Submit review
        self.driver.execute_script(
            "arguments[0].click();",
            submit_btn
        )

        # Wait after submit
        time.sleep(3)

        body = self.driver.find_element(By.TAG_NAME, "body")

        body.send_keys(Keys.ESCAPE)

        time.sleep(1)

        # Reopen product
        product = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".mat-card img")
            )
        )

        self.driver.execute_script(
            "arguments[0].click();",
            product
        )

        # Wait review render
        time.sleep(3)

        # Check XSS execution
        detected = self.driver.execute_script(
            "return window.xss_detected"
        )

        # Full page source
        page = self.driver.page_source
        if "&lt;img" in page:
            logger.info("Payload stored and escaped")

        if detected == "XSS_Review":

            logger.warning(
                f"[XSS] Stored XSS executed: {payload}"
            )

            self.result.append(
                ("Stored_XSS", "", "", payload)
            )

        elif payload in page:

            logger.warning(
                f"[HTML Injection] Payload stored but not executed: {payload}"
            )

            self.result.append(
                ("Stored_HTML_Injection", "", "", payload)
            )

        else:

            logger.debug(
                "Payload was not saved or was sanitized"
            )

    def test_stored_reflection_profile(self):
        rand_suffix = ''.join(random.choices(string.ascii_lowercase, k=6))
        email = f"stored_reflection_profile_{rand_suffix}@test.com"
        password = "Password123"
        if not self.register_user(email, password):
            logger.error("Registration failed")
            return
        if not self.login(email, password):
            logger.error("Login failed")
            return

        try:
            self.driver.get(f"{self.base_url}/profile")
            logger.info(f"Testing profile {self.base_url}/profile")
            payload = "PROFILE_REFLECT_TEST_123"
            #payload = (
                #'<img src=x '
                #'onerror="window.xss_detected=\'PROFILE_REFLECT\'">'
            #)
            #payload = "<b>HTML_TEST</b>"
            marker = "PROFILE_REFLECT"

            username = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username.clear()
            username.send_keys(payload)

            save_btn = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "submit"))
            )
            self.driver.execute_script("arguments[0].click();", save_btn)
            username_after = self.driver.find_element(By.ID, "username")
            print(f"Username: {username_after.get_attribute("value")}")
            time.sleep(2)
            self.driver.refresh()
            time.sleep(3)
            print(self.driver.find_element(By.ID, "username").get_attribute("value"))
            page = self.driver.page_source
            print(page)
            print(self.driver.execute_script("return window.xss_detected"))

            if marker in page:
                logger.warning(f"[Stored Reflection] Username persisted and reflected: {payload}")
                self.result.append(("Stored_Reflection_Profile", "", "", payload))
            else:
                logger.info("Stored Reflection не обнаружено")
        except Exception as e:
            logger.error(f"Failed Stored Reflection Profile: {e}")

    def test_profile_image(self):
        rand_suffix = ''.join(random.choices(string.ascii_lowercase, k=6))
        email = f"profile_image_{rand_suffix}@test.com"
        password = "Password123"
        if not self.register_user(email, password):
            logger.error("Registration failed")
            return
        if not self.login(email, password):
            logger.error(f"Login failed")
            return
        try:
            self.driver.get(f"{self.base_url}/profile")
            logger.info(f"Testing image profile {self.base_url}/profile")
            payload = """data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" onload="window.xss_detected='SVG'"/>"""


            input_url = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "url"))
            )
            input_url.clear()
            input_url.send_keys(payload)
            url_button = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "submitUrl"))
            )

            self.driver.execute_script("arguments[0].click();", url_button)
            url_after = self.driver.find_element(By.ID, "url")
            print(f"Url input: {url_after.get_attribute('value')}")
            time.sleep(2)
            self.driver.refresh()
            time.sleep(3)
            page = self.driver.page_source
            print(page)

            if payload in page:
                logger.warning(f"[Stored Reflection] Image URL reflected: {payload}]")
                self.result.append(("Stored_Reflection_Profile", payload, "", "", payload))
            else:
                logger.info(f"[Stored Reflection] Image URL not reflected")
        except Exception as e:
            logger.error(f"Failed Stored Reflection Profile Image: {e}")

    def test_registration_reflected_xss(self):
        rand_suffix = ''.join(random.choices(string.ascii_lowercase, k=6))
        email = f"xss_profile_{rand_suffix}@test.com"
        password = "Password123"
        answer = "SECURITY_TEST_ABC"
        answer1 = '<img src=x onerror="window.xss_detected=\'REGISTER_XSS\'">'

        try:
            self.driver.get(f"{self.base_url}/#/register")
            logger.info(f"Testing registration {self.base_url}/#/register")
            print("Current URL: ", self.driver.current_url)
            email_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "emailControl"))
            )
            email_input.clear()
            email_input.send_keys(email)

            password_input = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.ID, "passwordControl"))
            )
            password_input.clear()
            password_input.send_keys(password)

            repeat_password = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "repeatPasswordControl"))
            )
            repeat_password.clear()
            repeat_password.send_keys(password)

            question_select = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "mat-select"))
            )
            self.driver.execute_script("arguments[0].click();", question_select)

            question_option = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "mat-option"))
            )
            self.driver.execute_script("arguments[0].click();", question_option)

            answer_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "securityAnswerControl"))
            )
            answer_input.clear()
            answer_input.send_keys(answer1)
            print(answer_input.get_attribute("value"))

            register_button = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "registerButton"))
            )
            print(register_button.is_enabled())
            self.driver.execute_script("arguments[0].click();", register_button)

            time.sleep(2)

            page = self.driver.page_source

            print(self.driver.current_url)

            errors = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".error"
            )

            error = self.driver.find_elements(By.CSS_SELECTOR, ".mat-mdc-form-field-error")
            for p in error:
                print(f"Error: {p.text}")

            for e in errors:
                print(e.text)

            body = self.driver.find_element(
                By.TAG_NAME,
                "body"
            ).get_attribute("innerHTML")

            print("SECURITY_TEST_ABC" in body)

            if answer1 in page:
                logger.warning(f"[Reflection XSS] Answer reflected: {answer1}]")
            else:
                logger.info(f"[Reflection XSS] Answer not reflected")
        except Exception as e:
            logger.error(f"Failed Stored Reflection Registration: {e}")

    def test_saved_payment_xss_reflection(self):
        rand_suffix = ''.join(random.choices(string.ascii_lowercase, k=6))
        email = f"profile_image_{rand_suffix}@test.com"
        password = "Password123"
        card_number = '5555555555554444'
        payloads = [
            ("CARD_REFLECT_123", "REFLECTION"),
            ("<b>CARD_HTML</b>", "HTML"),
            ('<img src=x onerror="window.xss_detected=\'CARD_XSS\'">', "XSS"),
            ('" onmouseover="window.xss_detected=\'CARD_ATTR\'"', "ATTRIBUTE")
        ]
        if not self.register_user(email, password):
            logger.error("Registration failed")
            return
        if not self.login(email, password):
            logger.error(f"Login failed")
            return

        for payload, payload_type in payloads:
            try:
                logger.info(f"Testing Saved Payment payload: {payload}")
                self.driver.get(f"{self.base_url}/#/saved-payment-methods")
                print(self.driver.current_url)
                self.driver.execute_script("""window.xss_detected = null;""")

                header = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "mat-expansion-panel-header"))
                )
                self.driver.execute_script("arguments[0].click();", header)

                time.sleep(1)

                print("Header class:",
                      header.get_attribute("class"))

                print(
                    self.driver.execute_script("""
                        const p = document.querySelector("mat-expansion-panel");
                        return {
                            expanded: p.className,
                            aria: p.querySelector("mat-expansion-panel-header").getAttribute("aria-expanded")
                        };
                    """)
                )
                WebDriverWait(self.driver, 10).until(
                    lambda d: "mat-expanded" in d.find_element(
                        By.CSS_SELECTOR,
                        "mat-expansion-panel-header"
                    ).get_attribute("class")
                )

                inputs = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "mat-expansion-panel input"))
                )
                print(f"INPUTS FOUND: {inputs}")

                name_input = inputs[0]
                card_input = inputs[1]

                name_input.clear()
                name_input.send_keys(payload)
                name_input.send_keys(Keys.TAB)

                card_input.clear()
                card_input.send_keys(card_number)
                card_input.send_keys(Keys.TAB)

                selects = self.driver.find_elements(By.CSS_SELECTOR, "mat-expansion-panel select")

                month_select = Select(selects[0])
                month_select.select_by_visible_text("12")

                year_select = Select(selects[1])
                year_select.select_by_visible_text("2096")

                time.sleep(1)

                print("Name: ", name_input.get_attribute("value"))
                print("Card: ", card_input.get_attribute("value"))
                print("Month: ", month_select.first_selected_option.text)
                print("Year: ", year_select.first_selected_option.text)

                submit_button = self.driver.find_element(By.ID, "submitButton")
                print("Disable: ", submit_button.get_attribute("disabled"))
                print("Class: ", submit_button.get_attribute("class"))

                print(
                    self.driver.execute_script("""
                        return document.querySelectorAll('input')[0].value;
                    """)
                )

                print(
                    self.driver.execute_script("""
                        return document.querySelectorAll('input')[1].value;
                    """)
                )

                print(
                    self.driver.execute_script("""
                        return document.querySelectorAll('input')[0].className;
                    """)
                )

                print(
                    self.driver.execute_script("""
                        return document.querySelectorAll('input')[1].className;
                    """)
                )

                errors = self.driver.execute_script("""
                const controls = document.querySelectorAll('input');
                return Array.from(controls).map(e => ({
                    value: e.value,
                    valid: e.checkValidity(),
                    validation: e.validationMessage
                }));
                """)
                print(f"Errors: {errors}")

                self.driver.execute_script("arguments[0].click();", submit_button)

                time.sleep(2)
                self.driver.refresh()

                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "mat-table"))
                )
                body = self.driver.find_element(By.TAG_NAME, "body").get_attribute("innerHTML")

                detected = self.driver.execute_script("return window.xss_detected")
                rows = self.driver.find_elements(By.CSS_SELECTOR, "mat-row")

                print("=" * 80)
                print("TABLE CONTENT")
                print("=" * 80)

                found_reflection = False
                found_html = False
                found_attribute = False

                for row in rows:
                    cells = row.find_elements(By.CSS_SELECTOR, "mat-cell")

                    imgs = row.find_elements(By.CSS_SELECTOR, "img")

                    for img in imgs:
                        print(img.get_attribute("outerHTML"))

                    print(self.driver.execute_script("""
                    return Array.from(document.querySelectorAll('img'))
                        .map(i => i.outerHTML);
                    """))

                    print("-" * 80)

                    for cell in cells:

                        text = cell.text
                        html = cell.get_attribute("innerHTML")

                        print("TEXT: ", repr(text))
                        print("HTML: ", html)

                        if payload in text:
                            found_reflection = True
                        if cell.find_elements(By.TAG_NAME, "b"):
                            found_html = True
                        if self.driver.execute_script("return arguments[0].hasAttribute('onmouseover')", cell):
                            found_attribute = True
                    print("-" * 80)
                cards = self.driver.find_elements(By.CSS_SELECTOR, "app-payment-details")

                for card in cards:
                    print(card.get_attribute("outerHTML"))

                if detected:
                    logger.warning(f"[Stored XSS] Payload executed: {payload}")
                    self.result.append(("Stored XSS", payload, "", payload_type))

                if found_reflection:
                    logger.warning(f"[Stored Reflection] Payload detected: {payload}]")
                    self.result.append(("Stored Reflection_Payment", payload, "", payload_type))

                if found_html:
                    logger.warning(f"[Stored HTML] Payload executed: {payload}")
                    self.result.append(("Stored HTML_Payment", payload, "", payload_type))

                if found_attribute:
                    logger.warning(f"[Stored Attribute] Payload detected: {payload}")
                    self.result.append(("Stored Attribute_Payment", payload, "", payload_type))

            except Exception as e:
                logger.error(f"Saved Payment payload error: {payload} : {e}")
                logger.error(traceback.format_exc())

    def print_summary(self):
        logger.info("=" * 50)
        logger.info("        ОТЧЁТ СКАНЕРА УЯЗВИМОСТЕЙ")
        logger.info("=" * 50)
        if not self.result:
            logger.info("Уязвимостей не найдено.")
        else:
            logger.info(f"Всего найдено: {len(self.result)}")
            for vuln in self.result:
                vuln_type, url, param, payload = vuln
                logger.warning(f"[{vuln_type}] {url} | параметр: {param} | payload: {payload}")
        logger.info("=" * 50)

    def run_all(self):
        logger.info("=== Running XSS Testing via Selenium + Chrome ===")
        self.test_registration_reflected_xss()
        self.test_xss_review()
        self.test_search_reflection()
        self.test_stored_reflection_profile()
        self.test_profile_image()
        self.test_saved_payment_xss_reflection()
        self.print_summary()
        logger.info("=== XSS testing completed ===")
        self.driver.quit()

if __name__ == "__main__":
    tester = ScannerJuiceShopXSS(headless=True)
    tester.run_all()