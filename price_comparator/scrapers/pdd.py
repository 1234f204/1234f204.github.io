import random
from typing import List
from .base import BaseScraper
from ..models import Product

PDD_STORES = [
    ("拼多多官方旗舰店", 4.8), ("拼多多品牌店", 4.6), ("拼多多自营", 4.7),
    ("拼多多百亿补贴", 4.9), ("拼多多优选", 4.5), ("拼多多特卖店", 4.4),
    ("拼多多官方直营", 4.8), ("拼多多折扣店", 4.3),
]

PDD_NAME_SUFFIXES = [
    " 百亿补贴", " 万人团", " 官方补贴", "",
    " 限时秒杀", " 超值特惠", " 拼单价", " 限量版",
]


class PDDScraper(BaseScraper):
    platform_name = "拼多多"
    base_url = "https://mobile.yangkeduo.com"

    def search(self, keyword: str, count: int = 10) -> List[Product]:
        products = []
        base_price = self._estimate_base_price(keyword)
        for i in range(count):
            store, rating = random.choice(PDD_STORES)
            suffix = random.choice(PDD_NAME_SUFFIXES)
            price = round(base_price * random.uniform(0.6, 0.95), 2)
            original_price = round(price * random.uniform(1.2, 1.8), 2)
            sales = random.randint(1000, 5000000)
            goods_id = random.randint(100000000, 999999999)
            products.append(Product(
                name=f"{keyword}{suffix}",
                price=price,
                original_price=original_price,
                sales=sales,
                store_name=store,
                store_rating=rating,
                platform=self.platform_name,
                url=f"https://mobile.yangkeduo.com/goods.html?goods_id={goods_id}",
                keyword=keyword,
            ))
        return products

    @staticmethod
    def _estimate_base_price(keyword: str) -> float:
        price_hints = {
            "iphone": 4999, "手机": 1999, "电脑": 3999, "笔记本": 4499,
            "耳机": 199, "平板": 1799, "ipad": 2299, "电视": 2499,
            "冰箱": 2199, "洗衣机": 1599, "空调": 2099, "相机": 3499,
            "键盘": 199, "鼠标": 89, "显示器": 1199, "显卡": 3199,
            "内存": 299, "硬盘": 399, "音箱": 199, "手表": 799,
            "路由器": 129, "充电器": 39, "数据线": 9, "壳": 12,
            "鞋": 199, "衣服": 99, "包": 149, "食品": 29,
            "炸锅": 199, "空气": 199, "吹风机": 129, "净水器": 899,
            "扫地": 1799, "投影": 2299, "打印机": 699, "微波炉": 399,
            "电饭煲": 199, "豆浆机": 199, "吸尘器": 699, "加湿器": 99,
            "电动牙刷": 129, "剃须刀": 199, "体脂秤": 49, "台灯": 69,
        }
        kw_lower = keyword.lower()
        for hint, price in price_hints.items():
            if hint in kw_lower:
                return price * random.uniform(0.9, 1.1)
        return random.uniform(20, 4000)
