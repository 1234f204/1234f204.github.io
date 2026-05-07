import logging
import re
from typing import List
from selenium.webdriver.common.by import By
from ..models import Product
from .base import BaseScraper

logger = logging.getLogger(__name__)


class TaobaoScraper(BaseScraper):
    platform_name = "淘宝"
    base_url = "https://www.taobao.com"
    search_url = "https://s.taobao.com/search?q={keyword}"
    login_keywords = ["登录", "请登录", "login"]

    def search(self, keyword: str, count: int = 10) -> List[Product]:
        return self._scrape_with_selenium(keyword, count)

    def _parse_products(self, driver, keyword: str, count: int) -> List[Product]:
        products = []
        try:
            items = driver.find_elements(
                By.CSS_SELECTOR,
                ".Content--contentInner--QVTcU0M, "
                "[class*='Content--contentInner'], "
                ".Card--doubleCardWrapper, "
                "[class*='doubleCard'], "
                ".search-content-card, "
                "[class*='Card']",
            )
            if not items:
                items = driver.find_elements(
                    By.CSS_SELECTOR,
                    "[class*='item'], [class*='card'], [class*='product']",
                )
            for item in items[:count]:
                try:
                    product = self._parse_item(item, keyword)
                    if product and product.price > 0:
                        products.append(product)
                except Exception as e:
                    logger.debug("Taobao parse item error: %s", e)
                    continue
        except Exception as e:
            logger.warning("Taobao find items error: %s", e)
        return products

    def _parse_item(self, item, keyword: str) -> Product:
        name = ""
        try:
            name_el = item.find_element(
                By.CSS_SELECTOR,
                "[class*='title'], [class*='Title'], a[title]",
            )
            name = self._safe_text(name_el)
            if not name:
                name = self._safe_attr(item.find_element(By.CSS_SELECTOR, "a[title]"), "title")
        except Exception:
            pass

        price = 0.0
        try:
            price_el = item.find_element(
                By.CSS_SELECTOR,
                "[class*='price'], [class*='Price']",
            )
            price = self._extract_price(self._safe_text(price_el)) or 0.0
        except Exception:
            pass

        original_price = None
        try:
            op_els = item.find_elements(
                By.CSS_SELECTOR,
                "[class*='originalPrice'], [class*='OriginalPrice'], del",
            )
            for op_el in op_els:
                op = self._extract_price(self._safe_text(op_el))
                if op and op > price:
                    original_price = op
                    break
        except Exception:
            pass

        url = ""
        try:
            link = item.find_element(By.CSS_SELECTOR, "a[href]")
            url = self._safe_attr(link, "href")
            if url and not url.startswith("http"):
                url = "https:" + url
        except Exception:
            pass

        store_name = ""
        store_rating = 0.0
        try:
            store_el = item.find_element(
                By.CSS_SELECTOR,
                "[class*='shop'], [class*='Shop'], [class*='store']",
            )
            store_name = self._safe_text(store_el)
        except Exception:
            pass

        sales = 0
        try:
            sales_el = item.find_element(
                By.CSS_SELECTOR,
                "[class*='sell'], [class*='Sales'], [class*='payNum']",
            )
            sales_text = self._safe_text(sales_el)
            sales = self._parse_sales(sales_text)
        except Exception:
            pass

        return Product(
            name=name or keyword,
            price=price,
            original_price=original_price,
            sales=sales,
            store_name=store_name,
            store_rating=store_rating,
            platform=self.platform_name,
            url=url or f"https://s.taobao.com/search?q={keyword}",
            keyword=keyword,
        )

    @staticmethod
    def _parse_sales(text: str) -> int:
        if not text:
            return 0
        text = text.replace(",", "").replace(" ", "")
        if "万" in text:
            match = re.search(r"([\d.]+)万", text)
            if match:
                return int(float(match.group(1)) * 10000)
        if "千" in text:
            match = re.search(r"([\d.]+)千", text)
            if match:
                return int(float(match.group(1)) * 1000)
        match = re.search(r"(\d+)", text)
        return int(match.group(1)) if match else 0
