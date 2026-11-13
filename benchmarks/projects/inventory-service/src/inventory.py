class Inventory:
    def __init__(self, catalog):
        self.catalog = catalog

    def reserve_stock(self, sku, units):
        if units <= 0:
            raise ValueError('invalid quantity')
        item = self.catalog.find_item(sku)
        if item.stock < units:
            raise ValueError('insufficient stock')
        item.stock -= units

    def restore_stock(self, sku, units):
        if units < 0:
            raise ValueError('invalid quantity')
        self.catalog.find_item(sku).stock += units
