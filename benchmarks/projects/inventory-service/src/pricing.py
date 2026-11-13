def calculate_subtotal(lines):
    return sum(price * quantity for price, quantity in lines)

def apply_discount(subtotal_cents, percent):
    if not 0 <= percent <= 100:
        raise ValueError('invalid discount')
    return subtotal_cents * (100-percent) // 100

def calculate_tax(subtotal_cents, basis_points):
    return subtotal_cents * basis_points // 10000
