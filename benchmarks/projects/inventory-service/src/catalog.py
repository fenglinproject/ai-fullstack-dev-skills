from dataclasses import dataclass

@dataclass
class Item:
    sku: str
    price_cents: int
    stock: int

class Catalog:
    def __init__(self):
        self.items = {}

    def add_item(self, item):
        if item.price_cents < 0 or item.stock < 0:
            raise ValueError('invalid item')
        self.items[item.sku] = item

    def find_item(self, sku):
        return self.items[sku]
