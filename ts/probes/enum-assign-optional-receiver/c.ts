import { Phone1 as P1 } from './e1';
import { Phone1 as P2 } from './e2';

interface Phone { number: string; type: P1 }
const phone = { number: '1', type: P2.Mobile };
declare const pn: typeof phone | { number: string; type: P1 };
declare const pu: typeof phone | undefined;
declare const pl: typeof phone | null;
export const y2: Phone = pn;
export const y3 = pn as Phone;
export const y4 = pu as Phone;
export const y5 = pl as Phone;
export const y6 = pu! as Phone;
export const y7: Phone = pu!;
export function g(p: Phone) { return p; }
g(pn);
export const y8 = pu as Phone | undefined;
export const y9 = phone as Phone;
