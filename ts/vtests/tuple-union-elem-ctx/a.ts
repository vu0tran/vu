// An array literal in a union of tuples: each element's contextual type is the union of the
// tuples' elements there (not the last tuple's), so literals of any member keep their types.
const x: ['a', 1] | ['b', 2] = ['a', 1];
const y: ['a', 1] | ['b', 2] = ['b', 2];
type Pair = ['on', boolean] | ['size', number, string];
const p1: Pair[] = [['on', true], ['size', 3, 'px']];
const p2: Pair = ['size', 1, 'em'];
declare function take(xs: ReadonlyArray<[1, 'one'] | [2, 'two']>): void;
take([[1, 'one'], [2, 'two']]);
declare function pick<T extends ['a', 1] | ['b', 2, true]>(x: T): T;
const r1: number = pick(['a', 1]);
const r2: number = pick(['b', 2, true]);
declare function pick2<T extends [string, 'x'] | [number]>(x: T): T;
const r3: number = pick2(['s', 'x']);
const cb: [(x: { a: 1 }) => void, 'p'] | [number, 'q'] = [(x) => { const n: string = x.a; }, 'p'];
const cb2: [(x: { a: 1 }) => void, string] | [number, string] = [(x) => { const n: string = x.a; }, 'p'];
