import type { P } from './missing';
type M = Omit<P, '$typeName' | 'createdAt'> & { createdAt: Date | null };
declare const m: M;
const a: number = m.id;
const b: number = null! as M['id'];
const c: number = null! as Omit<P, 'x'>;
declare const p: P;
export function f(): M {
  return { id: p.id, createdAt: p.createdAt };
}
export function g(): Omit<P, 'x'> {
  return { id: p.id };
}
