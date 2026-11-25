from app.calculator import PriceCalculator
from app.models import OrderItem


class DiscountedPriceCalculator(PriceCalculator):
    """Strategy pattern: Pricing with volume discount"""
    
    def __init__(self, discount_percentage: float = 0):
        self.discount_percentage = discount_percentage
    
    def calculate_total(self, items: list) -> float:
        base_total = sum(item.quantity * item.unit_price for item in items)
        discount_amount = base_total * (self.discount_percentage / 100)
        total = base_total - discount_amount
        return round(total, 2)


class ProgressiveDiscountCalculator(PriceCalculator):
    """Strategy pattern: Progressive discount based on order amount"""
    
    def calculate_total(self, items: list) -> float:
        base_total = sum(item.quantity * item.unit_price for item in items)
        
        if base_total >= 500:
            discount_percentage = 15
        elif base_total >= 200:
            discount_percentage = 10
        elif base_total >= 100:
            discount_percentage = 5
        else:
            discount_percentage = 0
        
        discount_amount = base_total * (discount_percentage / 100)
        total = base_total - discount_amount
        return round(total, 2)
