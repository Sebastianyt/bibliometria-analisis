from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
import time
import os
from typing import List, Optional, Tuple


def _ebsco_providers_from_env() -> List[str]:
    """
    Lista de valores exactos del atributo value del checkbox en la faceta
    «Proveedor de contenido» (separados por coma). Ejemplo:
    Academic Search Ultimate,Business Source Complete
    """
    raw = (os.environ.get("BIBLIOMETRIA_EBSCO_PROVIDERS") or "").strip()
    if raw:
        return [p.strip() for p in raw.split(",") if p.strip()]
    return ["Academic Search Ultimate"]


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

    def _safe_click(self, element) -> None:
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(0.25)
        try:
            element.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", element)

    def _find_control_input_by_value(self, value: str):
        for el in self.driver.find_elements(By.CSS_SELECTOR, "input[data-auto='control-input']"):
            if (el.get_attribute("value") or "") == value:
                return el
        return None

    def _apply_content_provider_filter_in_current_context(
        self, provider_value: str, uncheck_providers: Optional[List[str]] = None
    ) -> bool:
        """
        Todos los filtros → Proveedor de contenido → (opcional) desmarcar otros → marcar proveedor → Aplicar.
        """
        wait = WebDriverWait(self.driver, 25)
        try:
            all_filters = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button[data-auto='all-filters-button'], #all-filter-button")
                )
            )
            self._safe_click(all_filters)
            time.sleep(1.2)

            facet_header = None
            for label_fragment in (
                "Proveedor de contenido",
                "Content Provider",
                "Content provider",
            ):
                facet_xpath = (
                    "//button[@data-auto='facet-header']"
                    "[.//span[@data-auto='facet-label']"
                    f"[contains(normalize-space(.), '{label_fragment}')]]"
                )
                try:
                    facet_header = WebDriverWait(self.driver, 6).until(
                        EC.element_to_be_clickable((By.XPATH, facet_xpath))
                    )
                    break
                except TimeoutException:
                    continue
            if facet_header is None:
                return False
            self._safe_click(facet_header)
            time.sleep(1.0)

            if uncheck_providers:
                for pname in uncheck_providers:
                    cb = self._find_control_input_by_value(pname)
                    if cb is not None and cb.is_selected():
                        self._safe_click(cb)
                        time.sleep(0.2)

            target = self._find_control_input_by_value(provider_value)
            if target is None:
                return False
            if not target.is_selected():
                self._safe_click(target)
            time.sleep(0.4)

            apply_btn = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button[data-auto='ebsco-filter-panel-apply-button']")
                )
            )
            self.driver.execute_script("arguments[0].click();", apply_btn)
            time.sleep(2.5)
            return True
        except Exception:
            return False

    def _switch_content_provider_in_current_context(self, from_provider: str, to_provider: str) -> bool:
        return self._apply_content_provider_filter_in_current_context(
            to_provider, uncheck_providers=[from_provider]
        )

    def _ensure_provider_filter_and_results_per_page_50(self, provider_value: str) -> bool:
        """Prueba cada marco: filtro por proveedor y Mostrar 50."""
        self.driver.switch_to.default_content()
        frames: List[Optional[object]] = [None]
        for iframe in self.driver.find_elements(By.TAG_NAME, "iframe"):
            frames.append(iframe)
        filter_ok = False
        fifty_ok = False
        for frame in frames:
            self.driver.switch_to.default_content()
            if frame is not None:
                self.driver.switch_to.frame(frame)
            try:
                if not self._apply_content_provider_filter_in_current_context(provider_value):
                    continue
                filter_ok = True
                print(f"✓ Filtros: Proveedor de contenido → {provider_value} → Aplicar.")
                if self._click_results_per_page_50_in_current_context():
                    fifty_ok = True
                    print("✓ Mostrar 50 seleccionado.")
                    print("   Esperando a que la lista de resultados se actualice…")
                    time.sleep(8)
                    return True
                print("⚠ Filtros OK pero no se pudo elegir Mostrar 50 en este marco; probando otro…")
            except Exception:
                pass
        self.driver.switch_to.default_content()
        if not filter_ok:
            print("⚠ No se aplicaron filtros EBSCO en ningún marco.")
        if not fifty_ok:
            print("⚠ Reintentando solo Mostrar 50…")
            if self._ensure_results_per_page_50():
                print("✓ Mostrar 50 aplicado (reintento).")
                return True
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
                    print("   Esperando a que la lista de resultados se actualice…")
                    time.sleep(8)
                    return True
            except Exception:
                pass
        self.driver.switch_to.default_content()
        return False

    def _bulk_select_all_on_page(self) -> bool:
        print("\n--- Checking page structure ---")
        try:
            self.driver.find_element(By.CSS_SELECTOR, "div.bulk-record_bulk-record__menu__RAbET")
            print("✓ Found bulk-record menu container!")
        except Exception as e:
            print(f"✗ Could not find bulk-record menu container: {e}")

        page_html = self.driver.page_source
        if "bulk-record" not in page_html:
            print("✗ Page HTML does NOT contain 'bulk-record' - waiting…")
            time.sleep(5)

        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        print("\n--- Checkbox selección masiva ---")
        checkbox = None
        for attempt in range(15):
            try:
                checkbox = self.driver.find_element(By.CSS_SELECTOR, "input[data-auto='bulk-record-checkbox']")
                self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                break
            except Exception:
                pass
            try:
                checkbox = self.driver.find_element(
                    By.CSS_SELECTOR, "input.bulk-record-checkbox_bulk-record__checkbox__eCMAy__input"
                )
                self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                break
            except Exception:
                pass
            try:
                checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                if checkboxes:
                    checkbox = checkboxes[0]
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", checkbox)
                    break
            except Exception:
                pass
            time.sleep(1)

        if checkbox is None:
            print("ERROR: No se encontró el checkbox de selección masiva.")
            return False

        self.driver.execute_script("arguments[0].click();", checkbox)
        print("✓ Checkbox masivo activado.")
        print("   Esperando a que cargue la barra de acciones masivas…")
        time.sleep(7)

        print("\n--- Desplegable: todos en esta página ---")
        dropdown_button = None
        for attempt in range(5):
            try:
                dropdown_button = self.driver.find_element(By.ID, "downshift-0-toggle-button")
                break
            except Exception:
                pass
            try:
                dropdown_button = self.driver.find_element(
                    By.CSS_SELECTOR, "button[data-auto='bulk-record-arrow-dropdown']"
                )
                break
            except Exception:
                pass
            time.sleep(1)

        if dropdown_button is None:
            print("ERROR: No se encontró el desplegable de cantidad.")
            return False

        self.driver.execute_script("arguments[0].click();", dropdown_button)
        time.sleep(4)

        select_all_option = None
        for attempt in range(5):
            try:
                select_all_option = self.driver.find_element(By.ID, "downshift-0-item-0")
                break
            except Exception:
                pass
            try:
                select_all_option = self.driver.find_element(
                    By.CSS_SELECTOR, "li[data-auto='arrow-dropdown-select-all-on-page-button']"
                )
                break
            except Exception:
                pass
            time.sleep(1)

        if select_all_option is None:
            print("ERROR: No se encontró «todos en esta página».")
            return False

        self.driver.execute_script("arguments[0].click();", select_all_option)
        print("✓ Todos los resultados de la página seleccionados.")
        time.sleep(5)
        return True

    def _wait_for_new_csv(self, existing_names: set, timeout: int = 120) -> Optional[str]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(1)
            try:
                names = os.listdir(self.download_dir)
            except OSError:
                continue
            for name in names:
                if not name.lower().endswith(".csv"):
                    continue
                if name in existing_names:
                    continue
                path = os.path.join(self.download_dir, name)
                try:
                    if os.path.getsize(path) > 0:
                        return path
                except OSError:
                    pass
        return None

    def _close_bulk_download_modal(self) -> bool:
        """Cierra el modal con Escape (más fiable que la X en EBSCO)."""
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.ESCAPE)
            time.sleep(0.45)
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(0.45)
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            time.sleep(1.5)
            print("✓ Modal cerrado con tecla Escape.")
            return True
        except Exception:
            pass
        wait = WebDriverWait(self.driver, 8)
        selectors = [
            (By.CSS_SELECTOR, "button[data-auto='close-button']"),
            (By.CSS_SELECTOR, "button.eb-modal__close-button[title='Cerrar']"),
            (By.CSS_SELECTOR, "button[aria-label='Cerrar']"),
            (By.CSS_SELECTOR, "button[aria-label='Close']"),
        ]
        for by, sel in selectors:
            try:
                btn = wait.until(EC.element_to_be_clickable((by, sel)))
                self.driver.execute_script("arguments[0].click();", btn)
                time.sleep(1.2)
                return True
            except Exception:
                continue
        return False

    def _download_csv_via_tool_button(self) -> Optional[str]:
        """Botón herramienta Descargar → modal → CSV → Descargar; espera al archivo."""
        existing_names = set(os.listdir(self.download_dir))
        wait = WebDriverWait(self.driver, 25)
        tool = None
        for by, sel in (
            (By.CSS_SELECTOR, "button[data-auto='tool-button'][aria-label='Descargar']"),
            (By.CSS_SELECTOR, "button[data-auto='tool-button'][aria-label='Download']"),
            (
                By.XPATH,
                "//button[@data-auto='tool-button' and (contains(@aria-label,'escargar') or contains(@aria-label,'ownload'))]",
            ),
        ):
            try:
                tool = wait.until(EC.element_to_be_clickable((by, sel)))
                break
            except TimeoutException:
                continue
        if tool is None:
            print("ERROR: No se encontró el botón de herramienta Descargar (data-auto=tool-button).")
            return None

        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tool)
        time.sleep(0.3)
        self.driver.execute_script("arguments[0].click();", tool)
        print("   Esperando a que el modal de descarga termine de abrir…")
        time.sleep(5)

        modal_wait = WebDriverWait(self.driver, 35)
        csv_radio = None
        csv_selectors = (
            "input[data-auto='bulk-download-formats-group-input'][name='metadata'][value='csv']",
            "fieldset[data-auto='bulk-download-formats-group-metadata'] "
            "input[data-auto='bulk-download-formats-group-input'][name='metadata'][value='csv']",
            "input[data-auto='bulk-download-formats-group-input'][value='csv']",
        )
        for sel in csv_selectors:
            try:
                csv_radio = modal_wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                break
            except TimeoutException:
                continue
        if csv_radio is None:
            print("ERROR: No apareció el radio CSV en el modal (bulk-download-formats-group-input).")
            return None

        print("   Esperando un momento más antes de elegir CSV…")
        time.sleep(4)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", csv_radio)
        time.sleep(0.8)
        try:
            label = csv_radio.find_element(By.XPATH, "./ancestor::label[1]")
            self.driver.execute_script("arguments[0].click();", label)
        except Exception:
            self.driver.execute_script("arguments[0].click();", csv_radio)
        if not csv_radio.is_selected():
            self.driver.execute_script("arguments[0].checked = true; arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", csv_radio)
        time.sleep(0.5)

        try:
            dl_btn = modal_wait.until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "button[data-auto='bulk-download-modal-download-button'][title='Descargar']",
                    )
                )
            )
        except TimeoutException:
            try:
                dl_btn = modal_wait.until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "button[data-auto='bulk-download-modal-download-button']")
                    )
                )
            except TimeoutException:
                print("ERROR: No se encontró el botón Descargar del modal.")
                return None

        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dl_btn)
        time.sleep(0.2)
        self.driver.execute_script("arguments[0].click();", dl_btn)
        print("Descarga CSV iniciada (modal)…")
        path = self._wait_for_new_csv(existing_names, timeout=120)
        if path is None:
            print("ERROR: No llegó ningún CSV nuevo a la carpeta de descargas.")
        return path

    def search_and_export(self, query: str) -> List[Tuple[str, str]]:
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
                return []
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
            return []

        print(f"Current URL: {self.driver.current_url}")
        try:
            self.driver.save_screenshot("results_page_screenshot.png")
            print("Screenshot saved as results_page_screenshot.png")
        except Exception:
            print("Could not save screenshot")

        print(f"Page title: {self.driver.title}")

        providers = _ebsco_providers_from_env()
        if not providers:
            providers = ["Academic Search Ultimate"]

        results: List[Tuple[str, str]] = []
        n = len(providers)

        for idx, provider in enumerate(providers):
            print(f"\n=== Proveedor EBSCO ({idx + 1}/{n}): {provider} ===")
            if idx == 0:
                print("\n--- Filtros → Mostrar 50 ---")
                self._ensure_provider_filter_and_results_per_page_50(provider)
            else:
                if not self._switch_content_provider_in_current_context(providers[idx - 1], provider):
                    print(f"ERROR: No se pudo cambiar de proveedor a «{provider}».")
                    break
                print("✓ Proveedor actualizado.")
                time.sleep(3)
                if not self._click_results_per_page_50_in_current_context():
                    self._ensure_results_per_page_50()
                print("   Esperando tras Mostrar 50…")
                time.sleep(6)

            if not self._bulk_select_all_on_page():
                print("ERROR: Selección masiva en página falló.")
                break

            print("Esperando un momento antes de abrir Descargar…")
            time.sleep(4)

            csv_path = self._download_csv_via_tool_button()
            if not csv_path:
                break
            results.append((provider, csv_path))

            if idx < n - 1:
                print("\n--- Cerrar modal antes de la siguiente base (Escape) ---")
                if not self._close_bulk_download_modal():
                    print("⚠ No se pudo cerrar el modal.")
                time.sleep(2)

        return results

    def close_browser(self):
        print("Closing browser...")
        if self.driver:
            self.driver.quit()
        print("Browser closed.")

def download_all_data(query: str, download_dir: str) -> List[Tuple[str, str]]:
    print("Initializing downloader...")
    downloader = DataDownloader(download_dir)
    downloader.start_browser()
    files = downloader.search_and_export(query)
    downloader.close_browser()
    return files