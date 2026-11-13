import { Checkout, Product } from './price';
export function invoiceTotal(items: Product[]): number {
  return new Checkout().calculate(items, 0.1);
}
