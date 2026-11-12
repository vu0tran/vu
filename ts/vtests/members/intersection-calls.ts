interface Callable { (name: string, fn?: () => void): number; (name: string, opts: { a: 1 }): string }
type Chain<F extends (...args: any) => any> = F & { only: Chain<F> } & { each: (x: number) => void };
declare const d: Chain<Callable>;
export const r1: string = d("x");
export const r2: string = d.only("x", { a: 1 });
d.each(1);
declare const e: ((x: number) => string) & { z: 1 };
export const r3: number = e(1);
