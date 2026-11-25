from abc import ABC, abstractmethod


class PriceCalculator(ABC):
    """Interface Segregation: Strategy pattern for price calculation"""
    
    @abstractmethod
    def calculate_total(self, items: list) -> float:
        pass


class StandardPriceCalculator(PriceCalculator):
    """Single Responsibility: Calculates order total"""
    
    def calculate_total(self, items: list) -> float:
        total = sum(item.quantity * item.unit_price for item in items)
        return round(total, 2)
