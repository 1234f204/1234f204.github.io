from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Product:
    name: str
    price: float
    platform: str
    url: str
    original_price: Optional[float] = None
    sales: int = 0
    store_name: str = ""
    store_rating: float = 0.0
    keyword: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    def to_dict(self):
        d = asdict(self)
        return d

    @property
    def discount_rate(self):
        if self.original_price and self.original_price > 0:
            return round(1 - self.price / self.original_price, 4)
        return 0.0


@dataclass
class PriceTrend:
    product_name: str
    platform: str
    dates: list
    prices: list

    def to_dict(self):
        return {
            "product_name": self.product_name,
            "platform": self.platform,
            "dates": self.dates,
            "prices": self.prices,
        }


@dataclass
class ComparisonResult:
    products: list
    best_price: Optional[Product] = None
    best_value: Optional[Product] = None
    price_range: tuple = (0.0, 0.0)
    avg_price: float = 0.0
    value_scores: list = field(default_factory=list)

    def to_dict(self):
        return {
            "products": [p.to_dict() if hasattr(p, "to_dict") else p for p in self.products],
            "best_price": self.best_price.to_dict() if self.best_price else None,
            "best_value": self.best_value.to_dict() if self.best_value else None,
            "price_range": list(self.price_range),
            "avg_price": self.avg_price,
            "value_scores": self.value_scores,
        }
