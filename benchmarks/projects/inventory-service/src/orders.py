from src.pricing import calculate_subtotal, apply_discount, calculate_tax

class OrderService:
    def __init__(self, inventory):
        self.inventory = inventory

    def place_order(self, sku, count, unit_price, discount_percent=0):
        self.inventory.reserve_stock(sku, count)
        subtotal = calculate_subtotal([(unit_price, count)])
        discounted = apply_discount(subtotal, discount_percent)
        return {'sku': sku, 'quantity': count, 'total_cents': discounted}

    def cancel_order(self, order):
        self.inventory.restore_stock(order['sku'], order['quantity'])
