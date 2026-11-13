export interface Product { price: number; quantity: number }
export function subtotal(items: Product[]): number {
  return items.reduce((total, item) => total + item.price * item.quantity, 0);
}
export class Checkout {
  calculate(items: Product[], discount: number): number {
    return Math.round(subtotal(items) * (1 - discount));
  }
}
