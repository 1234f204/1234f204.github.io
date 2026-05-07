import logging
import re
from typing import List
from selenium.webdriver.common.by import By
from ..models import Product
from .base import BaseScraper

logger = logging.getLogger(__name__)


class JDScraper(BaseScraper):
    platform_name = "京东"
    base_url = "https://www.jd.com"
    search_url = "https://search.jd.com/Search?keyword={keyword}&enc=utf-8"
    login_keywords = ["欢迎登录", "登录注册", "请登录"]

    def search(self, keyword: str, count: int = 10) -> List[Product]:
        return self._scrape_with_selenium(keyword, count)

    def _parse_products(self, driver, keyword: str, count: int) -> List[Product]:
        products = []
        try:
            items = driver.find_elements(By.CSS_SELECTOR, ".gl-item, [data-sku]")
            if not items:
                items = driver.find_elements(
                    By.CSS_SELECTOR, ".J-goods-list .gl-item, #J_goodsList li"
                )
            for item in items[:count]:
                try:
                    product = self._parse_item(item, keyword)
                    if product and product.price > 0:
                        products.append(product)
                except Exception as e:
                    logger.debug("JD parse item error: %s", e)
                    continue
        except Exception as e:
            logger.warning("JD find items error: %s", e)
        return products

    def _parse_item(self, item, keyword: str) -> Product:
        name = ""
        try:
            name_el = item.find_element(By.CSS_SELECTOR, ".p-name em, .p-name a em")
            name = self._safe_text(name_el)
        except Exception:
            try:
                name_el = item.find_element(By.CSS_SELECTOR, ".p-name a")
                name = self._safe_text(name_el)
            except Exception:
                pass

        price = 0.0
        try:
            price_el = item.find_element(
                By.CSS_SELECTOR, ".p-price i, .p-price strong i"
            )
            price = self._extract_price(self._safe_text(price_el)) or 0.0
        except Exception:
            pass

        original_price = None
        try:
            op_el = item.find_element(By.CSS_SELECTOR, ".p-price del, .p-origin-price")
            original_price = self._extract_price(self._safe_text(op_el))
        except Exception:
            pass

        url = ""
        try:
            link = item.find_element(By.CSS_SELECTOR, ".p-name a, .p-img a")
            url = self._safe_attr(link, "href")
            if url and not url.startswith("http"):
                url = "https:" + url
        except Exception:
            pass

        store_name = ""
        store_rating = 0.0
        try:
            store_el = item.find_element(
                By.CSS_SELECTOR, ".p-shop a, .J-hope-shop a"
            )
            store_name = self._safe_text(store_el)
        except Exception:
            pass

        sales = 0
        try:
            commit_el = item.find_element(
                By.CSS_SELECTOR, ".p-commit strong a, .p-commit a"
            )
            sales_text = self._safe_text(commit_el)
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
            url=url or f"https://search.jd.com/Search?keyword={keyword}",
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
