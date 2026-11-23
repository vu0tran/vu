import type { Bar } from './missing2';
export function g(p: Bar): number { return p ? 1 : 2; }
export const v: Bar = 1 as any;
export type Q = Bar;
