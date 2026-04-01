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
from typing import List, Optional, Tuple

SOURCE_ASU = "Academic Search Ultimate"
SOURCE_IEEE = "IEEE Xplore Digital Library"
BULK_EXPORT_FORMAT = "csv"


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

    def _apply_asu_content_provider_filter_in_current_context(self) -> bool:
        """
        Panel Todos los filtros → faceta Proveedor de contenido → Academic Search Ultimate → Aplicar.
        """
        wait = WebDriverWait(self.driver, 20)
        selectors_all_filters = (
            (By.CSS_SELECTOR, "button[data-auto='all-filters-button']"),
            (By.ID, "all-filter-button"),
        )
        all_filters = None
        for by, sel in selectors_all_filters:
            try:
                all_filters = wait.until(EC.element_to_be_clickable((by, sel)))
                break
            except TimeoutException:
                continue
        if all_filters is None:
            return False
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", all_filters)
        time.sleep(0.3)
        try:
            all_filters.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", all_filters)
        time.sleep(1.2)

        facet_xpath = (
            "//button[@data-auto='facet-header']"
            "[.//span[@data-auto='facet-label' and contains(normalize-space(), 'Proveedor de contenido')]]"
        )
        facet_btn = wait.until(EC.element_to_be_clickable((By.XPATH, facet_xpath)))
        try:
            facet_btn.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", facet_btn)
        time.sleep(1)

        asu_selector = "input[data-auto='control-input'][value='Academic Search Ultimate']"
        try:
            cb = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, asu_selector)))
        except TimeoutException:
            return False
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cb)
        time.sleep(0.2)
        if not cb.is_selected():
            try:
                cb.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", cb)

        apply_btn = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-auto='ebsco-filter-panel-apply-button']"))
        )
        try:
            apply_btn.click()
        except Exception:
            self.driver.execute_script("arguments[0].click();", apply_btn)
        time.sleep(4)
        return True

    def _ensure_asu_content_provider_filter(self) -> bool:
        """Ejecuta el filtro ASU en documento principal o en el iframe donde cargue EBSCO."""
        self.driver.switch_to.default_content()
        frames: List[Optional[object]] = [None]
        for iframe in self.driver.find_elements(By.TAG_NAME, "iframe"):
            frames.append(iframe)
        for frame in frames:
            self.driver.switch_to.default_content()
            if frame is not None:
                self.driver.switch_to.frame(frame)
            try:
                if self._apply_asu_content_provider_filter_in_current_context():
                    return True
            except Exception:
                pass
        self.driver.switch_to.default_content()
        return False

    @staticmethod
    def _click_element(driver, el) -> None:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
        time.sleep(0.25)
        try:
            el.click()
        except Exception:
            driver.execute_script("arguments[0].click();", el)

    def _snapshot_csv_paths(self) -> set:
        base = self.download_dir
        if not os.path.isdir(base):
            return set()
        return {
            os.path.join(base, f)
            for f in os.listdir(base)
            if f.lower().endswith(".csv")
        }

    def _wait_new_csv(self, before_paths: set, seconds: int = 90) -> Optional[str]:
        deadline = time.time() + seconds
        while time.time() < deadline:
            time.sleep(1.2)
            if not os.path.isdir(self.download_dir):
                continue
            for f in os.listdir(self.download_dir):
                if not f.lower().endswith(".csv"):
                    continue
                full = os.path.join(self.download_dir, f)
                if full not in before_paths:
                    return full
        return None

    def _open_all_filters_panel(self, wait: WebDriverWait):
        for by, sel in (
            (By.CSS_SELECTOR, "button[data-auto='all-filters-button']"),
            (By.ID, "all-filter-button"),
        ):
            try:
                btn = wait.until(EC.element_to_be_clickable((by, sel)))
                self._click_element(self.driver, btn)
                time.sleep(1)
                return
            except TimeoutException:
                continue
        raise TimeoutException("No se encontró el botón Todos los filtros.")

    def _open_proveedor_de_contenido_facet(self, wait: WebDriverWait):
        facet_xpath = (
            "//button[@data-auto='facet-header']"
            "[.//span[@data-auto='facet-label' and contains(normalize-space(), 'Proveedor de contenido')]]"
        )
        facet_btn = wait.until(EC.element_to_be_clickable((By.XPATH, facet_xpath)))
        self._click_element(self.driver, facet_btn)
        time.sleep(0.8)

    def _click_filter_panel_button_with_text(self, wait: WebDriverWait, text_exact: str) -> None:
        xp = (
            "//button[@data-auto='ebsco-filter-panel-apply-button']"
            f"[normalize-space()='{text_exact}']"
        )
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
        self._click_element(self.driver, btn)

    def _bulk_select_all_on_page_in_current_context(self) -> bool:
        """Marca checkbox de selección en bloque, abre flecha y elige todo en la página."""
        checkbox = None
        for _ in range(15):
            try:
                checkbox = self.driver.find_element(
                    By.CSS_SELECTOR, "input[data-auto='bulk-record-checkbox']"
                )
                break
            except Exception:
                pass
            try:
                checkbox = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "input.bulk-record-checkbox_bulk-record__checkbox__eCMAy__input",
                )
                break
            except Exception:
                pass
            try:
                boxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                if boxes:
                    checkbox = boxes[0]
                    break
            except Exception:
                pass
            time.sleep(1)
        if checkbox is None:
            return False
        self._click_element(self.driver, checkbox)
        time.sleep(1.2)

        dropdown_button = None
        for attempt in range(6):
            try:
                dropdown_button = self.driver.find_element(By.ID, "downshift-0-toggle-button")
                break
            except Exception:
                try:
                    dropdown_button = self.driver.find_element(
                        By.CSS_SELECTOR, "button[data-auto='bulk-record-arrow-dropdown']"
                    )
                    break
                except Exception:
                    time.sleep(0.6)
        if dropdown_button is None:
            return False
        self._click_element(self.driver, dropdown_button)
        time.sleep(1.2)

        select_all_option = None
        try:
            select_all_option = self.driver.find_element(By.ID, "downshift-0-item-0")
        except Exception:
            try:
                select_all_option = self.driver.find_element(
                    By.CSS_SELECTOR, "li[data-auto='arrow-dropdown-select-all-on-page-button']"
                )
            except Exception:
                pass
        if select_all_option is None:
            return False
        self._click_element(self.driver, select_all_option)
        time.sleep(2.8)
        return True

    def _find_download_tool_button(self):
        """El botón de herramienta Descargar; aria-label puede variar."""
        xpaths = (
            "//button[@data-auto='tool-button'][.//svg[@data-icon='download']]",
            "//button[@data-auto='tool-button' and (@aria-label='Descargar' or @title='Descargar')]",
        )
        for xp in xpaths:
            els = self.driver.find_elements(By.XPATH, xp)
            for el in els:
                try:
                    if el.is_displayed() and el.is_enabled():
                        return el
                except Exception:
                    continue
        return None

    def _click_download_tool_in_any_context(self) -> None:
        """
        La barra de herramientas con Descargar a veces está en el padre y el grid en iframe.
        Prueba el contexto actual primero, luego default y el resto de iframes.
        """
        time.sleep(0.6)
        contexts_tried = []

        def try_current() -> bool:
            tool = self._find_download_tool_button()
            if tool is not None:
                self._click_element(self.driver, tool)
                return True
            return False

        if try_current():
            return

        self.driver.switch_to.default_content()
        contexts_tried.append("default")
        if try_current():
            return

        for iframe in self.driver.find_elements(By.TAG_NAME, "iframe"):
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(iframe)
            contexts_tried.append("iframe")
            if try_current():
                return

        self.driver.switch_to.default_content()
        raise TimeoutException(
            "No se encontró el botón de herramienta Descargar (data-auto=tool-button + icono download). "
            f"Contextos probados: {contexts_tried}"
        )

    def _select_bulk_download_format_in_current_context(self, export_format: str) -> bool:
        """
        Elige el radio de formato en el modal EBSCO. Los inputs suelen ser 'decorativos':
        hay que clicar el <label> o usar click() por JavaScript en el input.
        """
        fs_sel = "fieldset[data-auto='bulk-download-formats-group-metadata']"
        wait = WebDriverWait(self.driver, 15)
        try:
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, fs_sel)))
        except TimeoutException:
            return False
        time.sleep(0.35)
        esc = export_format.replace("'", "\\'")
        label_xpath = (
            f"//fieldset[@data-auto='bulk-download-formats-group-metadata']"
            f"//input[@data-auto='bulk-download-formats-group-input'][@value='{esc}']/ancestor::label[1]"
        )
        try:
            label = self.driver.find_element(By.XPATH, label_xpath)
            self._click_element(self.driver, label)
            time.sleep(0.35)
            return True
        except Exception:
            pass
        css_inp = (
            f"{fs_sel} input[data-auto='bulk-download-formats-group-input'][value='{export_format}']"
        )
        try:
            inp = self.driver.find_element(By.CSS_SELECTOR, css_inp)
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", inp)
            time.sleep(0.15)
            self.driver.execute_script("arguments[0].click();", inp)
            time.sleep(0.25)
            if inp.is_selected():
                return True
        except Exception:
            pass
        try:
            txt = export_format.upper()
            span = self.driver.find_element(
                By.XPATH,
                (
                    "//fieldset[@data-auto='bulk-download-formats-group-metadata']"
                    f"//span[@data-auto='control-label-text' and normalize-space()='{txt}']"
                ),
            )
            self._click_element(self.driver, span)
            time.sleep(0.35)
            return True
        except Exception:
            pass
        return False

    def _complete_bulk_download_modal_in_any_context(self, export_format: str) -> None:
        """Tras abrir el tool, el modal puede estar en default o en el mismo iframe."""
        dl_sel = "button[data-auto='bulk-download-modal-download-button']"

        def try_fill_modal() -> bool:
            wait = WebDriverWait(self.driver, 18)
            try:
                wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "fieldset[data-auto='bulk-download-formats-group-metadata']")
                    )
                )
                time.sleep(0.4)
            except TimeoutException:
                return False
            if not self._select_bulk_download_format_in_current_context(export_format):
                return False
            time.sleep(0.45)
            try:
                dl = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, dl_sel)))
                self._click_element(self.driver, dl)
                return True
            except Exception:
                pass
            try:
                dl = self.driver.find_element(By.CSS_SELECTOR, dl_sel)
                self.driver.execute_script("arguments[0].click();", dl)
                return True
            except Exception:
                return False

        time.sleep(0.6)
        if try_fill_modal():
            return
        self.driver.switch_to.default_content()
        if try_fill_modal():
            return
        for iframe in self.driver.find_elements(By.TAG_NAME, "iframe"):
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(iframe)
            if try_fill_modal():
                return
        self.driver.switch_to.default_content()
        raise TimeoutException("No apareció el modal de descarga masiva (formato / botón Descargar).")

    def _download_tool_modal_confirm_in_current_context(self, export_format: str) -> None:
        """Tool Descargar (cualquier marco) → modal CSV → Descargar."""
        self._click_download_tool_in_any_context()
        time.sleep(1)
        self._complete_bulk_download_modal_in_any_context(export_format)

    def _force_click_element(self, el) -> None:
        """Clic agresivo para controles que Selenium marca como no interactuables."""
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center', inline:'center'});", el
        )
        time.sleep(0.12)
        try:
            el.click()
        except Exception:
            pass
        self.driver.execute_script(
            """
            var n = arguments[0];
            if (n && n.dispatchEvent) {
              n.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
            }
            if (n && typeof n.click === 'function') { try { n.click(); } catch (e) {} }
            """,
            el,
        )

    def _try_click_bulk_modal_close_in_current_context(self) -> bool:
        """
        Cierra el modal EBSCO. No usar solo is_displayed(): el overlay suele ser 'clicable'
        pero mal reportado. Prioriza el SVG xmark dentro del modal de descarga masiva.
        """
        xpaths_ordered = [
            "//div[contains(@class,'nuc-bulk-download-modal')]//button[@data-auto='close-button']",
            "//div[contains(@class,'nuc-bulk-download-modal')]//svg[@data-icon='xmark']/ancestor::button[1]",
            "//div[contains(@class,'eb-modal')]//button[@data-auto='close-button']",
            "//button[@data-auto='close-button' and contains(@class,'nuc-bulk-download-modal__close-button')]",
            "//button[@data-auto='close-button']",
            "//svg[@data-icon='xmark' and @data-prefix='fal']/ancestor::button[1]",
            "//button[.//svg[@data-icon='xmark']]",
            "//button[@title='Cerrar' and contains(@class,'eb-modal__close-button')]",
        ]
        for xp in xpaths_ordered:
            try:
                for el in self.driver.find_elements(By.XPATH, xp):
                    try:
                        self._force_click_element(el)
                        time.sleep(0.35)
                        return True
                    except Exception:
                        continue
            except Exception:
                pass
        try:
            for svg in self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'nuc-bulk-download-modal')]//svg[@data-icon='xmark']",
            ):
                try:
                    self._force_click_element(svg)
                    time.sleep(0.35)
                    return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def _try_escape_close_modal_in_current_context(self) -> bool:
        try:
            self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
            time.sleep(0.45)
            return True
        except Exception:
            return False

    def _close_bulk_download_modal_any_context(self) -> None:
        """
        Tras Descargar, el modal puede quedar abierto y bloquear filtros.
        Prueba contexto actual, documento principal e iframes.
        """
        time.sleep(1.1)

        def try_all_closes() -> bool:
            if self._try_click_bulk_modal_close_in_current_context():
                return True
            self._try_escape_close_modal_in_current_context()
            return self._try_click_bulk_modal_close_in_current_context()

        if try_all_closes():
            time.sleep(0.6)
            self.driver.switch_to.default_content()
            return
        self.driver.switch_to.default_content()
        if try_all_closes():
            time.sleep(0.6)
            return
        for iframe in self.driver.find_elements(By.TAG_NAME, "iframe"):
            self.driver.switch_to.default_content()
            self.driver.switch_to.frame(iframe)
            if try_all_closes():
                time.sleep(0.6)
                self.driver.switch_to.default_content()
                return
        self.driver.switch_to.default_content()
        print(
            "⚠ No se cerró el modal (close-button / xmark). "
            "Si sigue abierto, revisa el marco o cierra manualmente."
        )

    def _apply_asu_to_ieee_filter_switch_in_current_context(self) -> bool:
        """Quita ASU, aplica, elige IEEE (+ más), Actualizar selecciones, Aplicar."""
        wait = WebDriverWait(self.driver, 25)
        try:
            self._open_all_filters_panel(wait)
            self._open_proveedor_de_contenido_facet(wait)
            asu = wait.until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        f"input[data-auto='control-input'][value='{SOURCE_ASU}']",
                    )
                )
            )
            if asu.is_selected():
                self._click_element(self.driver, asu)
            time.sleep(0.4)
            self._click_filter_panel_button_with_text(wait, "Aplicar")
            time.sleep(4)

            self._open_all_filters_panel(wait)
            self._open_proveedor_de_contenido_facet(wait)
            try:
                more = WebDriverWait(self.driver, 8).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "button[data-auto='custom-show-more-button']")
                    )
                )
                self._click_element(self.driver, more)
                time.sleep(1)
            except TimeoutException:
                print("  (No apareció 'más' en proveedores; se intenta marcar IEEE igualmente.)")

            ieee = wait.until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        f"input[data-auto='control-input'][value='{SOURCE_IEEE}']",
                    )
                )
            )
            if not ieee.is_selected():
                self._click_element(self.driver, ieee)
            time.sleep(0.4)

            self._click_filter_panel_button_with_text(wait, "Actualizar selecciones")
            time.sleep(1.5)
            self._click_filter_panel_button_with_text(wait, "Aplicar")
            time.sleep(4)
            return True
        except Exception as e:
            print(f"Error cambiando filtro a IEEE: {e}")
            return False

    def _run_in_ebsco_frame(self, fn) -> bool:
        """Ejecuta fn() en default y en cada iframe hasta que retorne True."""
        self.driver.switch_to.default_content()
        frames: List[Optional[object]] = [None]
        for iframe in self.driver.find_elements(By.TAG_NAME, "iframe"):
            frames.append(iframe)
        for frame in frames:
            self.driver.switch_to.default_content()
            if frame is not None:
                self.driver.switch_to.frame(frame)
            try:
                if fn():
                    return True
            except Exception:
                pass
        self.driver.switch_to.default_content()
        return False

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

        print("\n--- Filtro: Proveedor de contenido → Academic Search Ultimate ---")
        if self._ensure_asu_content_provider_filter():
            print("✓ Filtro aplicado (Academic Search Ultimate).")
        else:
            print(
                "⚠ No se pudo aplicar el filtro de proveedor. "
                "Se continúa con los resultados sin restringir a ASU."
            )

        print("\n--- Mostrar 50 resultados por página ---")
        if self._ensure_results_per_page_50():
            print("✓ Seleccionado 'Mostrar 50' en el desplegable de resultados.")
        else:
            print(
                "⚠ No se pudo seleccionar 'Mostrar 50' (revisa el DOM o captura). "
                "Se continúa con la página tal cual."
            )

        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        downloads: List[Tuple[str, str]] = []

        print("\n--- [1/2] Descarga CSV: Academic Search Ultimate ---")
        if not self._run_in_ebsco_frame(lambda: self._bulk_select_all_on_page_in_current_context()):
            print("ERROR: No se pudo seleccionar todos los registros en página (ASU).")
            return []
        before_a = self._snapshot_csv_paths()
        try:
            self._download_tool_modal_confirm_in_current_context(BULK_EXPORT_FORMAT)
        except Exception as e:
            print(f"ERROR: Flujo de descarga (tool / modal) falló para ASU: {e}")
            return []
        path_asu = self._wait_new_csv(before_a)
        if not path_asu:
            print("ERROR: No llegó el CSV de Academic Search Ultimate.")
            return []
        print(f"✓ CSV ASU: {path_asu}")
        downloads.append((SOURCE_ASU, path_asu))
        print("Cerrando modal de descarga…")
        self._close_bulk_download_modal_any_context()

        print("\n--- Cambio de filtro: ASU → IEEE Xplore ---")
        if not self._run_in_ebsco_frame(lambda: self._apply_asu_to_ieee_filter_switch_in_current_context()):
            print("⚠ No se completó el cambio a IEEE; se devuelve solo el CSV de ASU.")
            return downloads

        print("\n--- Mostrar 50 (IEEE) ---")
        if not self._ensure_results_per_page_50():
            print("⚠ No se pudo reajustar Mostrar 50 tras el filtro IEEE.")

        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        print("\n--- [2/2] Descarga CSV: IEEE Xplore ---")
        if not self._run_in_ebsco_frame(lambda: self._bulk_select_all_on_page_in_current_context()):
            print("ERROR: No se pudo seleccionar todos los registros en página (IEEE).")
            return downloads
        before_i = self._snapshot_csv_paths()
        try:
            self._download_tool_modal_confirm_in_current_context(BULK_EXPORT_FORMAT)
        except Exception as e:
            print(f"ERROR: Flujo de descarga (tool / modal) falló para IEEE: {e}")
            return downloads
        path_ieee = self._wait_new_csv(before_i)
        if not path_ieee:
            print("ERROR: No llegó el CSV de IEEE Xplore.")
            return downloads
        print(f"✓ CSV IEEE: {path_ieee}")
        downloads.append((SOURCE_IEEE, path_ieee))
        print("Cerrando modal de descarga…")
        self._close_bulk_download_modal_any_context()
        return downloads

    def close_browser(self):
        print("Closing browser...")
        if self.driver:
            self.driver.quit()
        print("Browser closed.")

def download_all_data(query: str, download_dir: str) -> List[tuple]:
    print("Initializing downloader...")
    downloader = DataDownloader(download_dir)
    downloader.start_browser()
    paths = downloader.search_and_export(query)
    downloader.close_browser()
    return paths