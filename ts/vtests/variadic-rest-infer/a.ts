interface Arb<T> { gen(): T }
declare function str(): Arb<string>;
declare function num(): Arb<number>;
declare function property<Ts extends [unknown, ...unknown[]]>(...args: [...arbs: { [K in keyof Ts]: Arb<Ts[K]> }, pred: (...args: Ts) => boolean | void]): Ts;
const r1: string = property(str(), num(), (a, b) => { const x: number = a; const y: string = b; });
const r2 = property(str(), (a) => a.length > 1);
const r3: [number] = r2;
declare function tv<T extends unknown[]>(...args: [...T, (n: number) => void]): T;
const r4: string = tv(1, "a", (n) => { const z: string = n; });
export {};
