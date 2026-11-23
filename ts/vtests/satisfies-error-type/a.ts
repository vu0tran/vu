// `satisfies` an unresolved type: the expression is the error type (checkSatisfiesExpression).
import type { Missing } from './missing';

const input = { a: 'x' } satisfies Missing;
export const n: number = input;
const ok = { a: 'x' } satisfies { a: string };
export const m: number = ok;
