import random
from typing import List
from .base import BaseScraper
from ..models import Product

TB_STORES = [
    ("天猫官方旗舰店", 4.9), ("淘宝金牌卖家", 4.7), ("天猫超市", 4.8),
    ("淘宝企业店铺", 4.6), ("天猫国际官方", 4.9), ("淘宝品牌直营", 4.7),
    ("天猫甄选店", 4.8), ("淘宝优选店", 4.5),
]

TB_NAME_SUFFIXES = [
    " 天猫旗舰店", " 官方正品", " 包邮", "",
    " 新品上市", " 限时特惠", " 爆款", " 热销款",
]


class TaobaoScraper(BaseScraper):
    platform_name = "淘宝"
    base_url = "https://s.taobao.com"

    def search(self, keyword: str, count: int = 10) -> List[Product]:
        products = []
        base_price = self._estimate_base_price(keyword)
        for i in range(count):
            store, rating = random.choice(TB_STORES)
            suffix = random.choice(TB_NAME_SUFFIXES)
            price = round(base_price * random.uniform(0.75, 1.1), 2)
            original_price = round(price * random.uniform(1.1, 1.5), 2)
            sales = random.randint(100, 1000000)
            item_id = random.randint(100000000000, 999999999999)
            products.append(Product(
                name=f"{keyword}{suffix}",
                price=price,
                original_price=original_price,
                sales=sales,
                store_name=store,
                store_rating=rating,
                platform=self.platform_name,
                url=f"https://item.taobao.com/item.htm?id={item_id}",
                keyword=keyword,
            ))
        return products

    @staticmethod
    def _estimate_base_price(keyword: str) -> float:
        price_hints = {
            "iphone": 5599, "手机": 2599, "电脑": 4499, "笔记本": 4999,
            "耳机": 299, "平板": 2199, "ipad": 2699, "电视": 2999,
            "冰箱": 2599, "洗衣机": 1899, "空调": 2499, "相机": 3999,
            "键盘": 249, "鼠标": 129, "显示器": 1399, "显卡": 3599,
            "内存": 349, "硬盘": 449, "音箱": 249, "手表": 999,
            "路由器": 169, "充电器": 59, "数据线": 15, "壳": 19,
            "鞋": 299, "衣服": 149, "包": 199, "食品": 39,
            "炸锅": 259, "空气": 259, "吹风机": 169, "净水器": 1099,
            "扫地": 2199, "投影": 2699, "打印机": 899, "微波炉": 499,
            "电饭煲": 259, "豆浆机": 259, "吸尘器": 899, "加湿器": 129,
            "电动牙刷": 169, "剃须刀": 259, "体脂秤": 69, "台灯": 99,
        }
        kw_lower = keyword.lower()
        for hint, price in price_hints.items():
            if hint in kw_lower:
                return price * random.uniform(0.9, 1.1)
        return random.uniform(30, 4500)
