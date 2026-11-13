declare const rest: number[];
export const a: [string, ...number[]] = ['x', ...rest];
export const b: [string, ...string[]] = ['x', ...rest];
export const c: [string, number] = ['x', ...rest];
export const d: [string, ...number[]] = [1, ...rest];
export const e: readonly [string, ...number[]] = ['x', ...rest.map((n) => n * 2)];
const f: [string, ...number[]] = ['x', ...rest];
export const f2: 'z' = f;
