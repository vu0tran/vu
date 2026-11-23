declare function e1<T>(cases: readonly T[]): T;
const a1 = e1([{ f(): number { return 1; }, message: 'a' }]);
const n1: number = a1;
declare function e3<T>(cases: ReadonlyArray<T>): (fn: (a: T) => void) => void;
e3([
  { kind: 'object', error: { toString(): string { return 'x'; } }, message: 'm' },
  { kind: 'number', error: 42, message: '42' },
])(({ error, message }) => {
  const m: number = message;
  const e: number = error;
});
declare function e4<T>(cases: readonly { run: (x: T) => void; seed: T }[]): T;
const a4 = e4([{ run: (x) => {}, seed: 1 }]);
const n4: string = a4;
