interface Ret<T extends any[]> {
  (name: string | Function, fn: (...args: T) => void | Promise<void>, options?: number): void;
  (name: string | Function, options: { timeout?: number }, fn: (...args: T) => void | Promise<void>): void;
}
interface Each {
  <T extends any[] | [any]>(cases: ReadonlyArray<T>): Ret<T>;
  <T extends ReadonlyArray<any>>(cases: ReadonlyArray<T>): Ret<T extends Readonly<[any]> ? [T[0]] : Array<T extends ReadonlyArray<infer U> ? U : any>>;
  <T>(cases: ReadonlyArray<T>): Ret<T[]>;
}
declare const each: Each;
const al = { Http: true, Postgres: true, Redis: true, Express: true };
each([{ g: al, e: [] }, { g: {}, e: [] }, { g: { Http: true }, e: ['Http'] }, { g: { Postgres: true, Redis: false }, e: ['Postgres'] }])('t', ({ e }) => { const a: null = e; });
declare function f<T>(cases: ReadonlyArray<T>): T;
const al2 = { H: true, P: true, R: true, E: true };
const r5 = f([{ g: al2 }, { g: { H: true } }, { g: { P: true, R: false } }]);
r5.g.H;
const u1 = [{ a: 1, b: undefined }, { a: 2 }];
const u2 = [{ a: 1, b: 'x' }, { a: 2 }];
u1[0].b; u2[0].b;
