from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
import time
import os
from typing import List, Optional

class DataDownloader:
    def __init__(self, download_dir: str):
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
        self.driver = None

    def start_browser(self):
        print("Starting browser...")
        options = webdriver.ChromeOptions()

        # Evita el popup de "¿Quieres acceder a Chrome?" al loguearte con Google
        options.add_argument("--disable-features=ChromeSigninTriggerOnGaiaSignin")

        options.add_experimental_option("prefs", {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True
        })
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        print("Browser started.")

    def login_to_library(self, username: str, password: str):
        print("Logging in...")
        self.driver.get("https://library.uniquindio.edu.co/user/patron")
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, "name")))
        self.driver.find_element(By.NAME, "name").send_keys(username)
        self.driver.find_element(By.NAME, "pass").send_keys(password)
        self.driver.find_element(By.ID, "edit-submit").click()
        time.sleep(5)
        print("Logged in.")

    @staticmethod
    def _url_looks_like_ebsco_results(url: str) -> bool:
        u = url.lower()
        return any(
            h in u
            for h in (
                "ebscohost.com",
                "research-ebsco",
                "crai.referencistas.com",
                "referencistas.com",
            )
        )

    def _click_results_per_page_50_in_current_context(self) -> bool:
        """Abre el desplegable 'Mostrar' y elige 50 en el contexto actual (default o iframe)."""
        wait = WebDriverWait(self.driver, 15)
        toggle = None
        for by, sel in (
            (By.ID, "results-per-page-dropdown-toggle-button"),
            (By.CSS_SELECTOR, "button[data-auto='results-per-page-dropdown-toggle']"),
        ):
            try:
                toggle = wait.until(EC.element_to_be_clickable((by, sel)))
                break
            except TimeoutException:
                continue
        if toggle is None:
            return False
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", toggle)
        time.sleep(0.4)
        try:
            toggle.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", toggle)
        menu = wait.until(EC.visibility_of_element_located((By.ID, "results-per-page-dropdown-menu")))
        try:
            item = menu.find_element(
                By.XPATH,
                ".//button[@role='menuitem' and normalize-space()='50']",
            )
            self.driver.execute_script("arguments[0].click();", item)
            return True
        except Exception:
            pass
        for el in menu.find_elements(By.CSS_SELECTOR, "button[role='menuitem'], [role='menuitem']"):
            text = (el.text or "").strip()
            if text == "50" or (text.startswith("50") and "500" not in text and len(text) <= 4):
                self.driver.execute_script("arguments[0].click();", el)
                return True
        try:
            item = menu.find_element(
                By.XPATH,
                ".//*[self::button or @role='menuitem'][contains(normalize-space(.), '50') and not(contains(., '500'))]",
            )
            self.driver.execute_script("arguments[0].click();", item)
            return True
        except Exception:
            return False

    def _ensure_results_per_page_50(self) -> bool:
        """Prueba documento principal y cada iframe hasta encontrar el control EBSCO."""
        self.driver.switch_to.default_content()
        frames: List[Optional[object]] = [None]
        for iframe in self.driver.find_elements(By.TAG_NAME, "iframe"):
            frames.append(iframe)
        for frame in frames:
            self.driver.switch_to.default_content()
            if frame is not None:
                self.driver.switch_to.frame(frame)
            try:
                if self._click_results_per_page_50_in_current_context():
                    time.sleep(2)
                    return True
            except Exception:
                pass
        self.driver.switch_to.default_content()
        return False

    def search_and_export(self, query: str) -> str:
        print("Going to databases page...")
        self.driver.get("https://library.uniquindio.edu.co/databases")
        print("Current URL after get: " + self.driver.current_url)
        WebDriverWait(self.driver, 120).until(EC.presence_of_element_located((By.ID, "edit-search-form-stacks-external-catalogs-customdescubridor-eds-search-bar-container-query")))
        print("Search box found")
        print("Searching...")
        search_box = self.driver.find_element(By.ID, "edit-search-form-stacks-external-catalogs-customdescubridor-eds-search-bar-container-query")
        search_box.send_keys(query)
        print("Query entered")
        print("Waiting 3 seconds before clicking...")
        time.sleep(3)
        print("3 seconds elapsed, now clicking submit")
        submit_button = self.driver.find_element(By.ID, "edit-search-form-stacks-external-catalogs-customdescubridor-eds-search-bar-container-actions-submit")
        print("Submit button found")
        self.driver.execute_script("arguments[0].click();", submit_button)
        print("JavaScript click executed")
        time.sleep(2)
        print("Clicked, current url: " + self.driver.current_url)
        if len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(self.driver.window_handles[-1])
            print("Switched to new window, url: " + self.driver.current_url)
        print("Search submitted, checking for login...")
        try:
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, "btn-google")))
            print("Login form appeared, clicking Google login...")
            google_button = self.driver.find_element(By.ID, "btn-google")
            google_button.click()
            print("Google login clicked, entering credentials...")
            WebDriverWait(self.driver, 20).until(EC.url_contains("accounts.google.com"))
            print("On Google page")
            email_field = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "identifierId")))
            email_field.send_keys("sebastiand.espanag@uqvirtual.edu.co" + Keys.RETURN)
            print("Email entered and submitted, waiting 3 seconds...")
            time.sleep(3)
            print("Looking for password field...")
            password_field = None
            for attempt in range(10):
                try:
                    password_field = self.driver.find_element(By.NAME, "Passwd")
                    print(f"Found password field by name='Passwd' on attempt {attempt + 1}")
                    break
                except:
                    pass
                try:
                    password_field = self.driver.find_element(By.ID, "password")
                    print(f"Found password field by ID on attempt {attempt + 1}")
                    break
                except:
                    pass
                print(f"Attempt {attempt + 1}/10: Password field not found, waiting 3 more seconds...")
                time.sleep(3)
            if password_field is None:
                print("ERROR: Could not find password field after 30 seconds!")
                print("Current URL: " + self.driver.current_url)
                return None
            print("Password field found! Entering password...")
            password_field.send_keys("geamx100familia007")
            print("Password typed. Pressing Enter...")
            password_field.send_keys(Keys.RETURN)
            print("Password submitted")
            print("Waiting for redirect to EBSCO / CRAI (Ezproxy)...")
            WebDriverWait(self.driver, 90).until(
                lambda d: self._url_looks_like_ebsco_results(d.current_url)
            )
            print("✓ Logged in, waiting for results UI...")
            time.sleep(4)
        except Exception as e:
            print(f"Login process failed: {e}")
            return None

        print(f"Current URL: {self.driver.current_url}")
        try:
            self.driver.save_screenshot("results_page_screenshot.png")
            print("Screenshot saved as results_page_screenshot.png")
        except Exception:
            print("Could not save screenshot")

        print(f"Page title: {self.driver.title}")

        print("\n--- Mostrar 50 resultados por página ---")
        if self._ensure_results_per_page_50():
            print("✓ Seleccionado 'Mostrar 50' en el desplegable de resultados.")
        else:
            print(
                "⚠ No se pudo seleccionar 'Mostrar 50' (revisa el DOM o captura). "
                "Se continúa con la página tal cual."
            )

        print("\n--- Checking page structure ---")
        try:
            bulk_menu = self.driver.find_element(By.CSS_SELECTOR, "div.bulk-record_bulk-record__menu__RAbET")
            print("✓ Found bulk-record menu container!")
        except Exception as e:
            print(f"✗ Could not find bulk-record menu container: {e}")

        page_html = self.driver.page_source
        if "bulk-record" in page_html:
            print("✓ Page HTML contains 'bulk-record'")
        else:
            print("✗ Page HTML does NOT contain 'bulk-record' - interface not loaded!")
            print("Waiting 5 more seconds and retrying...")
            time.sleep(5)

        print("\n--- Scrolling to find elements ---")
        self.driver.execute_script("window.scrollTo(0, 0);")
        print("Scrolled to top of page")
        time.sleep(2)

        print("\n--- Looking for checkbox ---")
        checkbox = None
        for attempt in range(15):
            try:
                checkbox = self.driver.find_element(By.CSS_SELECTOR, "input[data-auto='bulk-record-checkbox']")
                print(f"✓ Attempt {attempt + 1}: Checkbox found by data-auto selector!")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                break
            except:
                pass
            try:
                checkbox = self.driver.find_element(By.CSS_SELECTOR, "input.bulk-record-checkbox_bulk-record__checkbox__eCMAy__input")
                print(f"✓ Attempt {attempt + 1}: Checkbox found by class selector!")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                break
            except:
                pass
            try:
                checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                if checkboxes:
                    checkbox = checkboxes[0]
                    print(f"✓ Attempt {attempt + 1}: Found first checkbox on page!")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                    break
            except:
                pass
            print(f"  Waiting 1 second before retry {attempt + 2}...")
            time.sleep(1)

        if checkbox is None:
            print("\n✗✗✗ ERROR: Could not find checkbox after all attempts ✗✗✗")
            return None

        self.driver.execute_script("arguments[0].click();", checkbox)
        print("Checkbox clicked using JavaScript")
        time.sleep(3)

        print("\nOpening dropdown for quantity selection...")
        dropdown_button = None
        for attempt in range(5):
            try:
                dropdown_button = self.driver.find_element(By.ID, "downshift-0-toggle-button")
                print("Found dropdown button by ID")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", dropdown_button)
                break
            except:
                try:
                    dropdown_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-auto='bulk-record-arrow-dropdown']")
                    print("Found dropdown button by data-auto")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", dropdown_button)
                    break
                except:
                    print(f"Attempt {attempt + 1}: Dropdown button not found, waiting...")
                    time.sleep(1)

        if dropdown_button is None:
            print("ERROR: Could not find dropdown button")
            return None

        self.driver.execute_script("arguments[0].click();", dropdown_button)
        print("Dropdown opened using JavaScript")
        time.sleep(3)

        print("\nSelecting 'All on this page'...")
        select_all_option = None
        for attempt in range(5):
            try:
                select_all_option = self.driver.find_element(By.ID, "downshift-0-item-0")
                print("Found select all option by ID")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", select_all_option)
                break
            except:
                try:
                    select_all_option = self.driver.find_element(By.CSS_SELECTOR, "li[data-auto='arrow-dropdown-select-all-on-page-button']")
                    print("Found select all option by data-auto")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", select_all_option)
                    break
                except:
                    print(f"Attempt {attempt + 1}: Select all option not found, waiting...")
                    time.sleep(1)

        if select_all_option is None:
            print("ERROR: Could not find select all option")
            return None

        self.driver.execute_script("arguments[0].click();", select_all_option)
        print("Selected all on page using JavaScript")
        time.sleep(3)

        print("Selecting CSV format...")
        csv_radio = None
        for attempt in range(5):
            try:
                csv_radio = self.driver.find_element(By.CSS_SELECTOR, "input[value='csv']")
                print("Found CSV radio button")
                break
            except:
                print(f"Attempt {attempt + 1}: CSV radio not found, waiting...")
                time.sleep(1)

        if csv_radio is None:
            print("ERROR: Could not find CSV radio button")
            return None

        self.driver.execute_script("arguments[0].click();", csv_radio)
        print("CSV format selected using JavaScript")
        time.sleep(2)

        print("Clicking download button...")
        download_button = None
        for attempt in range(5):
            try:
                download_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-auto='bulk-download-modal-download-button']")
                print("Found download button")
                break
            except:
                try:
                    download_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Descargar')]")
                    print("Found download button by text")
                    break
                except:
                    print(f"Attempt {attempt + 1}: Download button not found, waiting...")
                    time.sleep(1)

        if download_button is None:
            print("ERROR: Could not find download button")
            return None

        self.driver.execute_script("arguments[0].click();", download_button)
        print("Download button clicked using JavaScript")
        print("Waiting 15 seconds for download...")
        time.sleep(15)

        files = os.listdir(self.download_dir)
        print(f"Files in {self.download_dir}: {files}")
        csv_files = [f for f in files if f.endswith('.csv')]
        if csv_files:
            latest_csv = max([os.path.join(self.download_dir, f) for f in csv_files], key=os.path.getctime)
            print(f"Downloaded file: {latest_csv}")
            return latest_csv

        print("No CSV file found in download directory")
        return None

    def close_browser(self):
        print("Closing browser...")
        if self.driver:
            self.driver.quit()
        print("Browser closed.")

def download_all_data(query: str, download_dir: str) -> List[tuple]:
    print("Initializing downloader...")
    downloader = DataDownloader(download_dir)
    downloader.start_browser()
    file_path = downloader.search_and_export(query)
    downloader.close_browser()
    if file_path:
        return [('Unified', file_path)]
    return []