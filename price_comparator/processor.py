from typing import List, Optional
from difflib import SequenceMatcher
from .models import Product


class DataProcessor:
    def __init__(self, similarity_threshold: float = 0.7):
        self.similarity_threshold = similarity_threshold

    def process(self, products: List[Product], sort_by: str = "price") -> List[Product]:
        cleaned = self.clean(products)
        deduped = self.deduplicate(cleaned)
        sorted_products = self.sort_by(deduped, sort_by)
        return sorted_products

    def clean(self, products: List[Product]) -> List[Product]:
        result = []
        seen_ids = set()
        for p in products:
            if p.id in seen_ids:
                continue
            seen_ids.add(p.id)
            if not p.name or not p.name.strip():
                continue
            if p.price <= 0:
                continue
            p.name = p.name.strip()
            p.price = round(float(p.price), 2)
            if p.original_price and p.original_price < p.price:
                p.original_price = p.price
            if p.original_price:
                p.original_price = round(float(p.original_price), 2)
            p.sales = max(0, int(p.sales))
            p.store_rating = max(0.0, min(5.0, float(p.store_rating)))
            result.append(p)
        return result

    def deduplicate(self, products: List[Product]) -> List[Product]:
        if not products:
            return []
        groups = []
        for p in products:
            merged = False
            for group in groups:
                for existing in group:
                    if (p.platform == existing.platform and
                            self._name_similarity(p.name, existing.name) >= self.similarity_threshold):
                        if p.sales > existing.sales or p.store_rating > existing.store_rating:
                            group.append(p)
                        merged = True
                        break
                if merged:
                    break
            if not merged:
                groups.append([p])
        result = []
        for group in groups:
            best = max(group, key=lambda x: (x.store_rating, x.sales))
            result.append(best)
        return result

    def sort_by(self, products: List[Product], key: str = "price") -> List[Product]:
        sort_keys = {
            "price": lambda p: p.price,
            "sales": lambda p: -p.sales,
            "rating": lambda p: -p.store_rating,
            "discount": lambda p: -p.discount_rate,
        }
        if key not in sort_keys:
            key = "price"
        return sorted(products, key=sort_keys[key])

    def filter_by_platform(self, products: List[Product], platform: Optional[str] = None) -> List[Product]:
        if not platform:
            return products
        return [p for p in products if p.platform == platform]

    def filter_by_price_range(self, products: List[Product], min_price: float = 0, max_price: float = float("inf")) -> List[Product]:
        return [p for p in products if min_price <= p.price <= max_price]

    @staticmethod
    def _name_similarity(name1: str, name2: str) -> float:
        return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
