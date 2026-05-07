import os
import glob
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

_driver = None
_chromedriver_path = None


def _find_chromedriver():
    global _chromedriver_path
    if _chromedriver_path:
        return _chromedriver_path
    search_paths = [
        os.path.expanduser("~/.wdm/drivers/chromedriver"),
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
    ]
    for base in search_paths:
        if os.path.isdir(base):
            matches = glob.glob(os.path.join(base, "**/chromedriver"), recursive=True)
            if matches:
                _chromedriver_path = matches[0]
                return _chromedriver_path
        elif os.path.isfile(base):
            _chromedriver_path = base
            return _chromedriver_path
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        _chromedriver_path = ChromeDriverManager().install()
        return _chromedriver_path
    except Exception:
        pass
    return None


def get_driver():
    global _driver
    if _driver is not None:
        try:
            _driver.current_url
            return _driver
        except Exception:
            _driver = None
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver_path = _find_chromedriver()
    service = Service(executable_path=driver_path) if driver_path else Service()
    _driver = webdriver.Chrome(service=service, options=options)
    _driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )
    _driver.set_page_load_timeout(20)
    return _driver


def quit_driver():
    global _driver
    if _driver:
        try:
            _driver.quit()
        except Exception:
            pass
        _driver = None
