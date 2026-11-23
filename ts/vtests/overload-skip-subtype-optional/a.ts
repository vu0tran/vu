// chooseOverload's first pass with several candidates is by the subtype relation, and a function
// argument is anyFunctionType there: an options object type's optional properties are required
// (it isn't an object literal), so it(name, options?, fn?) doesn't fit and doesn't fix the
// callback's parameters before it(name, fn?) does (node:test's it in @types/node 20)
interface Opts { a?: number; b?: string }
interface Ctx { x: number }
type Fn = (t: Ctx, done: () => void) => void | Promise<void>;
declare function it(name?: string, options?: Opts, fn?: Fn): void;
declare function it(name?: string, fn?: Fn): void;
it('x', async (t) => { const a: number = t; });
it('y', (t) => { const b: number = t; });
it('z', async () => { const c: number = 's'; });

// an empty object type: the first fits
declare function h(o: {}): void;
declare function h(fn: Fn): void;
h((t) => { const e: number = t; });

// an object literal: its optional properties aren't required
declare function k(o: { f?: (n: number) => void; z?: number }): void;
declare function k(fn: Fn): void;
k({ f: (n) => { const s: string = n; } });

// a single candidate: by assignability
declare function one(o?: Opts): void;
one((t) => { const u: number = t; });

// anyFunctionType has the global Function's properties: it fits Function, and a type parameter
// constrained to it (MockTracker.method's implementation in @types/node 20)
declare function mk(o: Opts): void;
declare function mk<I extends Function>(impl: I): I;
const f = mk(async (u, v) => 1);
const fv: number = f;
declare function fx(o: Opts): void;
declare function fx(f: Function): string;
const fy: number = fx((w) => 1);
