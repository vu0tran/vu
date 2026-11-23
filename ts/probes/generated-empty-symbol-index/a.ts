// A symbol index signature makes a type not empty (a test: (e as Record<symbol, unknown>)[MARK]).
declare const e: unknown;
const MARK: unique symbol = Symbol('mark');
export const url = (e as Record<symbol, unknown>)[MARK];
export type Keys = Record<symbol, number>;
