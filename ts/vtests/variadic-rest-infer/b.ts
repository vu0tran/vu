interface Arb<T> { gen(): T }
declare function str(): Arb<string>;
declare function num(): Arb<number>;
declare function prop<Ts extends unknown[]>(...args: [...arbs: { [K in keyof Ts]: Arb<Ts[K]> }, pred: (...args: Ts) => boolean]): Ts;
const r0: string = prop(() => true);
declare function tv<T extends unknown[]>(...args: [...T, (n: number) => void, string]): T;
const r1: number = tv(1, (n) => {}, "s");
tv(1, (n) => {}, 2);
declare function cb<T extends unknown[]>(...args: [...T, (...a: T) => void]): T;
const r2: string = cb((x: number) => x, 1, (f, n) => { const q: string = n; });
declare function cs<T extends [string, ...string[]]>(...args: [...T, () => void]): T;
const r3: number = cs("a", "b", () => {});
export {};
