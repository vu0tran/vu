type A = (c: { u: string }, n: () => void) => number;
type B = (c: { u: string }, n: () => void) => Promise<void>;
type D = (c: number) => void;
declare function on(h: A | B): void;
on((c) => { const x: number = c.u; return 1; });
declare function on2(h: A | D): void;
on2((c) => 1);
