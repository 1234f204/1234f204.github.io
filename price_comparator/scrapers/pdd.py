import logging
import re
from typing import List
from selenium.webdriver.common.by import By
from ..models import Product
from .base import BaseScraper

logger = logging.getLogger(__name__)


class PDDScraper(BaseScraper):
    platform_name = "拼多多"
    base_url = "https://mobile.yangkeduo.com"
    search_url = "https://mobile.yangkeduo.com/search_result.html?search_key={keyword}"
    login_keywords = ["登录", "请登录", "login"]

    def search(self, keyword: str, count: int = 10) -> List[Product]:
        return self._scrape_with_selenium(keyword, count)

    def _parse_products(self, driver, keyword: str, count: int) -> List[Product]:
        products = []
        try:
            items = driver.find_elements(
                By.CSS_SELECTOR,
                "[class*='goodsList'] [class*='item'], "
                "[class*='search-result'] [class*='item'], "
                "[class*='product'], "
                "[class*='goods-item'], "
                "[class*='GoodsList'] a",
            )
            if not items:
                items = driver.find_elements(
                    By.CSS_SELECTOR,
                    "[class*='item'], [class*='card'], [class*='goods']",
                )
            for item in items[:count]:
                try:
                    product = self._parse_item(item, keyword)
                    if product and product.price > 0:
                        products.append(product)
                except Exception as e:
                    logger.debug("PDD parse item error: %s", e)
                    continue
        except Exception as e:
            logger.warning("PDD find items error: %s", e)
        return products

    def _parse_item(self, item, keyword: str) -> Product:
        name = ""
        try:
            name_el = item.find_element(
                By.CSS_SELECTOR,
                "[class*='name'], [class*='title'], [class*='Name']",
            )
            name = self._safe_text(name_el)
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
                "[class*='origin'], [class*='Origin'], del",
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
            try:
                url = self._safe_attr(item, "href")
                if url and not url.startswith("http"):
                    url = "https:" + url
            except Exception:
                pass

        store_name = ""
        store_rating = 0.0
        try:
            store_el = item.find_element(
                By.CSS_SELECTOR,
                "[class*='mall'], [class*='store'], [class*='shop']",
            )
            store_name = self._safe_text(store_el)
        except Exception:
            pass

        sales = 0
        try:
            sales_el = item.find_element(
                By.CSS_SELECTOR,
                "[class*='sales'], [class*='Sales'], [class*='sell']",
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
            url=url or f"https://mobile.yangkeduo.com/search_result.html?search_key={keyword}",
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
        match = re.search(r"(\d+)", text)
        return int(match.group(1)) if match else 0
