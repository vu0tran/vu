import { Phone1 as P1 } from './e1';
import { Phone1 as P2 } from './e2';

interface Phone { number: string; type: P1 }
interface Other { k: number }
const phone = { number: '1', type: P2.Mobile };
export const x1: Phone | undefined = phone;
export const x2: Phone | null = phone;
export const x3: Phone | Other = phone;
export const x4: (Phone | undefined)[] = [phone];
export const x5: P1 | undefined = P2.Mobile;
export const x6: { t: P1 | undefined } = { t: P2.Mobile };
export const x7: { p: Phone | undefined } = { p: phone };
export const x8: { p: { q: Phone | undefined } } = { p: { q: phone } };
declare const pu: typeof phone | undefined;
export const x9: Phone = pu as Phone;
export function f(p?: Phone) { return p; }
f(phone);
