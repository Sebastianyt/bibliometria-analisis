from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
from typing import List

class DataDownloader:
    def __init__(self, download_dir: str):
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)
        self.driver = None

    def start_browser(self):
        print("Starting browser...")
        options = webdriver.ChromeOptions()
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
        # Patron login
        self.driver.get("https://library.uniquindio.edu.co/user/patron")
        # Wait for login form
        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, "name")))
        self.driver.find_element(By.NAME, "name").send_keys(username)
        self.driver.find_element(By.NAME, "pass").send_keys(password)
        self.driver.find_element(By.ID, "edit-submit").click()
        # Wait for login
        time.sleep(5)
        print("Logged in.")

    def search_and_export(self, query: str) -> str:
        print("Going to databases page...")
        # Go to databases page
        self.driver.get("https://library.uniquindio.edu.co/databases")
        print("Current URL after get: " + self.driver.current_url)
        # Wait for page load
        WebDriverWait(self.driver, 120).until(EC.presence_of_element_located((By.ID, "edit-search-form-stacks-external-catalogs-customdescubridor-eds-search-bar-container-query")))
        print("Search box found")
        print("Searching...")
        # Search
        search_box = self.driver.find_element(By.ID, "edit-search-form-stacks-external-catalogs-customdescubridor-eds-search-bar-container-query")
        search_box.send_keys(query)
        print("Query entered")
        # Wait a bit
        print("Waiting 3 seconds before clicking...")
        time.sleep(3)
        print("3 seconds elapsed, now clicking submit")
        submit_button = self.driver.find_element(By.ID, "edit-search-form-stacks-external-catalogs-customdescubridor-eds-search-bar-container-actions-submit")
        print("Submit button found")
        # Use JavaScript click
        self.driver.execute_script("arguments[0].click();", submit_button)
        print("JavaScript click executed")
        time.sleep(2)  # Wait for navigation or new tab
        print("Clicked, current url: " + self.driver.current_url)
        # Check for new window
        if len(self.driver.window_handles) > 1:
            self.driver.switch_to.window(self.driver.window_handles[-1])
            print("Switched to new window, url: " + self.driver.current_url)
        print("Search submitted, checking for login...")
        # Check if login form appeared
        try:
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.ID, "btn-google")))
            print("Login form appeared, clicking Google login...")
            google_button = self.driver.find_element(By.ID, "btn-google")
            google_button.click()
            print("Google login clicked, entering credentials...")
            # Wait for Google login page
            WebDriverWait(self.driver, 20).until(EC.url_contains("accounts.google.com"))
            print("On Google page")
            # Enter email
            email_field = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.ID, "identifierId")))
            email_field.send_keys("sebastiand.espanag@uqvirtual.edu.co" + Keys.RETURN)
            print("Email entered and submitted, waiting 3 seconds...")
            time.sleep(3)
            
            # Wait for password field to appear - be very patient
            print("Looking for password field...")
            password_field = None
            
            for attempt in range(10):
                try:
                    # Try name="Passwd" (capital P - Google's actual attribute)
                    password_field = self.driver.find_element(By.NAME, "Passwd")
                    print(f"Found password field by name='Passwd' on attempt {attempt + 1}")
                    break
                except:
                    pass
                
                try:
                    # Try ID
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
            print("Typing: geamx100familia007")
            password_field.send_keys("geamx100familia007")
            print("Password typed. Pressing Enter...")
            password_field.send_keys(Keys.RETURN)
            print("Password submitted")
            print("Credentials entered, waiting for login and redirect to EBSCO...")
            # Wait for redirect back to EBSCO (give it more time)
            WebDriverWait(self.driver, 60).until(EC.url_contains("ebscohost.com"))
            print("Logged in to EBSCO, waiting 20 seconds for page to fully load...")
            time.sleep(20)
            print("Page loaded, continuing with download...")
        except Exception as e:
            print(f"Login process failed: {e}")
            return None
        # Print current page state for debugging
        print("Waiting for results page to fully load...")
        print(f"Current URL: {self.driver.current_url}")
        
        # Wait longer for React to render
        time.sleep(10)
        
        # Take a screenshot for debugging
        try:
            self.driver.save_screenshot("results_page_screenshot.png")
            print("Screenshot saved as results_page_screenshot.png")
        except:
            print("Could not save screenshot")
        
        # Check if there are any iframes and switch to main content
        try:
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            print(f"Found {len(iframes)} iframes on page")
            if iframes:
                self.driver.switch_to.frame(iframes[0])
                print("Switched to first iframe")
        except:
            print("No iframes or could not switch")
        
        # Print page title
        print(f"Page title: {self.driver.title}")
        
        # Try to find bulk menu container and print page structure
        print("\n--- Checking page structure ---")
        bulk_menu = None
        try:
            bulk_menu = self.driver.find_element(By.CSS_SELECTOR, "div.bulk-record_bulk-record__menu__RAbET")
            print("✓ Found bulk-record menu container!")
        except Exception as e:
            print(f"✗ Could not find bulk-record menu container: {e}")
        
        # Check if bulk-record text exists in HTML
        page_html = self.driver.page_source
        if "bulk-record" in page_html:
            print("✓ Page HTML contains 'bulk-record'")
        else:
            print("✗ Page HTML does NOT contain 'bulk-record' - interface not loaded!")
            print("Waiting 5 more seconds and retrying...")
            time.sleep(5)
        
        # Try scrolling to top to find the bulk record section
        print("\n--- Scrolling to find elements ---")
        self.driver.execute_script("window.scrollTo(0, 0);")
        print("Scrolled to top of page")
        time.sleep(2)
        
        # Select all records - wait for checkbox to be visible
        print("\n--- Looking for checkbox ---")
        checkbox = None
        for attempt in range(15):
            try:
                checkbox = self.driver.find_element(By.CSS_SELECTOR, "input[data-auto='bulk-record-checkbox']")
                print(f"✓ Attempt {attempt + 1}: Checkbox found by data-auto selector!")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                print("Scrolled checkbox into view")
                break
            except Exception as e:
                print(f"✗ Attempt {attempt + 1}: data-auto selector failed")
                
                # Try by class
                try:
                    checkbox = self.driver.find_element(By.CSS_SELECTOR, "input.bulk-record-checkbox_bulk-record__checkbox__eCMAy__input")
                    print(f"✓ Attempt {attempt + 1}: Checkbox found by class selector!")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                    print("Scrolled checkbox into view")
                    break
                except:
                    pass
                
                # Try finding by any checkbox in bulk menu
                try:
                    checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                    if checkboxes:
                        checkbox = checkboxes[0]
                        print(f"✓ Attempt {attempt + 1}: Found first checkbox on page!")
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                        print("Scrolled checkbox into view")
                        break
                except:
                    pass
                
                print(f"  Waiting 1 second before retry {attempt + 2}...")
                time.sleep(1)
        
        if checkbox is None:
            print("\n✗✗✗ ERROR: Could not find checkbox after all attempts ✗✗✗")
            print("Page may not have loaded correctly. Check results_page_screenshot.png")
            return None
        
        self.driver.execute_script("arguments[0].click();", checkbox)
        print("Checkbox clicked using JavaScript")
        time.sleep(3)
        
        # Open dropdown for quantity selection
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
        
        # Select "All on this page"
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
        
        # Select CSV format
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
        
        # Click Download button
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
        
        # Wait for download
        print("Waiting 15 seconds for download...")
        time.sleep(15)
        
        # Find the downloaded CSV file
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