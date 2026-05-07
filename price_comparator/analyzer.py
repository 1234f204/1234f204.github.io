import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .models import Product, PriceTrend, ComparisonResult


class DataAnalyzer:
    def __init__(self, price_weight: float = 0.4, sales_weight: float = 0.3, rating_weight: float = 0.3):
        self.price_weight = price_weight
        self.sales_weight = sales_weight
        self.rating_weight = rating_weight

    def compare(self, products: List[Product]) -> ComparisonResult:
        if not products:
            return ComparisonResult(products=[])

        prices = [p.price for p in products]
        best_price = min(products, key=lambda p: p.price)
        value_scores = self._calc_value_scores(products)
        best_value_idx = max(range(len(value_scores)), key=lambda i: value_scores[i]["score"])
        best_value = products[best_value_idx]

        return ComparisonResult(
            products=products,
            best_price=best_price,
            best_value=best_value,
            price_range=(min(prices), max(prices)),
            avg_price=round(sum(prices) / len(prices), 2),
            value_scores=value_scores,
        )

    def generate_trends(self, products: List[Product], days: int = 7) -> List[PriceTrend]:
        trends = []
        today = datetime.now()
        dates = [(today - timedelta(days=i)).strftime("%m-%d") for i in range(days - 1, -1, -1)]

        platform_groups: Dict[str, List[Product]] = {}
        for p in products:
            platform_groups.setdefault(p.platform, []).append(p)

        for platform, prods in platform_groups.items():
            avg_price = sum(p.price for p in prods) / len(prods)
            prices = []
            for i in range(days):
                variation = avg_price * random.uniform(-0.08, 0.08)
                if i == days - 1:
                    prices.append(round(avg_price, 2))
                else:
                    prices.append(round(avg_price + variation, 2))
            trends.append(PriceTrend(
                product_name=f"{prods[0].keyword} ({platform}均价)",
                platform=platform,
                dates=dates,
                prices=prices,
            ))
        return trends

    def get_platform_summary(self, products: List[Product]) -> List[Dict[str, Any]]:
        platform_groups: Dict[str, List[Product]] = {}
        for p in products:
            platform_groups.setdefault(p.platform, []).append(p)

        summary = []
        for platform, prods in platform_groups.items():
            prices = [p.price for p in prods]
            summary.append({
                "platform": platform,
                "count": len(prods),
                "avg_price": round(sum(prices) / len(prices), 2),
                "min_price": min(prices),
                "max_price": max(prices),
                "avg_rating": round(sum(p.store_rating for p in prods) / len(prods), 2),
                "total_sales": sum(p.sales for p in prods),
            })
        return sorted(summary, key=lambda x: x["avg_price"])

    def _calc_value_scores(self, products: List[Product]) -> List[Dict[str, Any]]:
        if not products:
            return []
        max_price = max(p.price for p in products) or 1
        max_sales = max(p.sales for p in products) or 1

        scores = []
        for p in products:
            norm_price = 1 - (p.price / max_price)
            norm_sales = p.sales / max_sales
            norm_rating = p.store_rating / 5.0
            score = (
                self.price_weight * norm_price
                + self.sales_weight * norm_sales
                + self.rating_weight * norm_rating
            )
            scores.append({
                "product_id": p.id,
                "product_name": p.name,
                "platform": p.platform,
                "price": p.price,
                "score": round(score, 4),
                "details": {
                    "price_score": round(norm_price, 4),
                    "sales_score": round(norm_sales, 4),
                    "rating_score": round(norm_rating, 4),
                },
            })
        return sorted(scores, key=lambda x: -x["score"])
