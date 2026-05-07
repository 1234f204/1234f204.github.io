from abc import ABC, abstractmethod
from typing import List
from ..models import Product


class BaseScraper(ABC):
    platform_name: str = ""
    base_url: str = ""

    @abstractmethod
    def search(self, keyword: str, count: int = 10) -> List[Product]:
        raise NotImplementedError

    def _build_url(self, keyword: str) -> str:
        return f"{self.base_url}/search?q={keyword}"
