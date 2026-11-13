import unittest
from src.catalog import Catalog, Item
from src.inventory import Inventory
from src.orders import OrderService

class OrderTests(unittest.TestCase):
    def test_checkout(self):
        catalog = Catalog()
        catalog.add_item(Item('A', 1200, 3))
        svc = OrderService(Inventory(catalog))
        order = svc.place_order('A', 2, 1200, 10)
        self.assertEqual(order['total_cents'], 2160)
        svc.cancel_order(order)
        self.assertEqual(catalog.find_item('A').stock, 3)

if __name__ == '__main__':
    unittest.main()
