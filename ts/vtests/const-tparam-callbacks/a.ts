// an object literal with callbacks for a const type parameter: its functions contextually typed by
// the parameter's constraint, the literal then as const
type Cfg<C> = { initial: string; ctx: C; on?: Record<string, (c: C) => C>; tag?: string };
interface Machine<C> { create<const T extends Cfg<C>>(cfg: T): T }
declare const m: Machine<{ n: number }>;
const a = m.create({ initial: 'idle', ctx: { n: 1 }, on: { INC: (c) => ({ n: c.n + 1 }) } });
export const x: number = a.initial;
