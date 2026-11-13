import { invoiceTotal } from '../src/invoice';
const total = invoiceTotal([{ price: 250, quantity: 2 }]);
if (total !== 450) throw new Error(`expected 450, received ${total}`);
