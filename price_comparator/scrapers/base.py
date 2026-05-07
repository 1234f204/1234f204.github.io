import logging
import re
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    NoSuchElementException,
)
from ..models import Product
from .driver import get_driver

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    platform_name: str = ""
    base_url: str = ""
    search_url: str = ""
    login_keywords: List[str] = []

    @abstractmethod
    def search(self, keyword: str, count: int = 10) -> List[Product]:
        raise NotImplementedError

    def _scrape_with_selenium(self, keyword: str, count: int) -> List[Product]:
        driver = get_driver()
        try:
            url = self._build_search_url(keyword)
            logger.info("[%s] Navigating to %s", self.platform_name, url)
            driver.get(url)
            time.sleep(2)
            self._wait_for_page(driver)
            if self._requires_login(driver):
                logger.warning("[%s] Login required, cannot scrape", self.platform_name)
                return []
            return self._parse_products(driver, keyword, count)
        except TimeoutException:
            logger.warning("[%s] Page load timeout for keyword: %s", self.platform_name, keyword)
            return []
        except WebDriverException as e:
            logger.error("[%s] WebDriver error: %s", self.platform_name, e)
            return []
        except Exception as e:
            logger.error("[%s] Unexpected error: %s", self.platform_name, e)
            return []

    def _build_search_url(self, keyword: str) -> str:
        return self.search_url.format(keyword=keyword)

    def _wait_for_page(self, driver):
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except TimeoutException:
            pass

    def _requires_login(self, driver) -> bool:
        page_text = driver.page_source.lower()
        title = driver.title.lower()
        for kw in self.login_keywords:
            if kw in page_text or kw in title:
                return True
        return False

    def _parse_products(self, driver, keyword: str, count: int) -> List[Product]:
        raise NotImplementedError

    @staticmethod
    def _extract_price(text: str) -> Optional[float]:
        if not text:
            return None
        matches = re.findall(r"[\d,]+\.?\d*", text.replace(",", ""))
        for m in matches:
            try:
                price = float(m)
                if price > 0:
                    return price
            except ValueError:
                continue
        return None

    @staticmethod
    def _safe_text(element) -> str:
        try:
            return element.text.strip()
        except Exception:
            return ""

    @staticmethod
    def _safe_attr(element, attr: str) -> str:
        try:
            return element.get_attribute(attr) or ""
        except Exception:
            return ""
