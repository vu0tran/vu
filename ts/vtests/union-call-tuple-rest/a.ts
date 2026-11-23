type MF<D, V> = (...[options]: {} extends V ? [options?: { variables?: V }] : [options: { variables: V }]) => Promise<D>;
declare const f1: MF<number, { id: string }>;
declare const f2: MF<string, { id: string; co?: number }>;
declare const b: boolean;
const m = b ? f1 : f2;
export const r: Promise<boolean> = m({ variables: { id: 'x' } });
export const r2 = m({ variables: { id: 1 } });
