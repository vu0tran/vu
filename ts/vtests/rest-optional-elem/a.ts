// A rest parameter's optional tuple element reads with undefined, as an optional parameter does.
declare const g: (...args: [string, number?]) => void;
export const g2: (a: string, b?: number) => void = g;
export const g3: (a: string, b: number) => void = g;
export const g4: (...args: [string, number?]) => void = (a: string, b?: number) => {};
export const g5: (...args: [string, number?]) => void = (a: string, b: number) => {};
type F = (input: string, init?: number) => Promise<string>;
declare const h: { (...args: Parameters<F>): ReturnType<F> } & { extra: 1 };
export const h2: F = h;
