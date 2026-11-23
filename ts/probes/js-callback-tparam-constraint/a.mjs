// an arrow given to a type parameter constrained to a function type, in JavaScript: its
// parameter takes the constraint's (nothing inferred, no default: not AnyDefault's any)
import { s } from './d.js';
export const a = s.refine((value) => new URL(value));
const raw = JSON.parse('{}');
export const b = s.refine((value) => raw.ok && new URL(value));
// (a type parameter inside the contextual signature, Array.from's T, with nothing inferred: any)
export const c = Array.from(raw.list, ([, name]) => name.trim());
