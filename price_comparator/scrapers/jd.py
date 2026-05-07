import random
from typing import List
from .base import BaseScraper
from ..models import Product

JD_STORES = [
    ("京东自营", 4.9), ("京东官方旗舰店", 4.8), ("京东数码专营店", 4.7),
    ("京东家电专营店", 4.6), ("京东超市自营", 4.9), ("京东国际自营", 4.8),
    ("京东电脑数码旗舰店", 4.7), ("京东生活馆", 4.5),
]

JD_NAME_SUFFIXES = [
    " 京东自营", " 官方旗舰店", " 京东专供", "",
    " 2024新款", " 升级版", " 标配版", " 尊享版",
]


class JDScraper(BaseScraper):
    platform_name = "京东"
    base_url = "https://search.jd.com"

    def search(self, keyword: str, count: int = 10) -> List[Product]:
        products = []
        base_price = self._estimate_base_price(keyword)
        for i in range(count):
            store, rating = random.choice(JD_STORES)
            suffix = random.choice(JD_NAME_SUFFIXES)
            price = round(base_price * random.uniform(0.85, 1.15), 2)
            original_price = round(price * random.uniform(1.05, 1.3), 2)
            sales = random.randint(500, 500000)
            product_id = f"jd_{random.randint(10000000, 99999999)}"
            products.append(Product(
                name=f"{keyword}{suffix}",
                price=price,
                original_price=original_price,
                sales=sales,
                store_name=store,
                store_rating=rating,
                platform=self.platform_name,
                url=f"https://item.jd.com/{product_id}.html",
                keyword=keyword,
            ))
        return products

    @staticmethod
    def _estimate_base_price(keyword: str) -> float:
        price_hints = {
            "iphone": 5999, "手机": 2999, "电脑": 4999, "笔记本": 5499,
            "耳机": 399, "平板": 2499, "ipad": 2999, "电视": 3299,
            "冰箱": 2999, "洗衣机": 2199, "空调": 2799, "相机": 4599,
            "键盘": 299, "鼠标": 149, "显示器": 1599, "显卡": 3999,
            "内存": 399, "硬盘": 499, "音箱": 299, "手表": 1299,
            "路由器": 199, "充电器": 79, "数据线": 19, "壳": 29,
            "鞋": 399, "衣服": 199, "包": 299, "食品": 49,
            "炸锅": 299, "空气": 299, "吹风机": 199, "净水器": 1299,
            "扫地": 2499, "投影": 2999, "打印机": 999, "微波炉": 599,
            "电饭煲": 299, "豆浆机": 299, "吸尘器": 999, "加湿器": 149,
            "电动牙刷": 199, "剃须刀": 299, "体脂秤": 79, "台灯": 129,
        }
        kw_lower = keyword.lower()
        for hint, price in price_hints.items():
            if hint in kw_lower:
                return price * random.uniform(0.9, 1.1)
        return random.uniform(50, 5000)
