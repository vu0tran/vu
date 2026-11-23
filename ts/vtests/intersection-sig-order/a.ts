// An intersection's members' signatures, in order: the first member's generic method is tried
// first (reorderCandidates puts another symbol's after all before it), as testing-library's
// BoundFunctions<typeof queries> & { [P in keyof Q]: BoundFunction<Q[P]> } has getByRole.
interface A { a: 1 }
interface B extends A { b: 1 }
declare const p: { g<T extends A = A>(r: string): T } & { g: (r: string) => A };
const b1: B = p.g('x');
declare const q: { g(r: string): A } & { g<T extends A = A>(r: string): T };
const b2: B = q.g('x');
// (merged declarations of one interface: the later one's overloads first)
interface M { m(r: string): A }
interface M { m<T extends A = A>(r: string): T }
declare const m: M;
const b3: B = m.m('x');
interface N { n<T extends A = A>(r: string): T }
interface N { n(r: string): A }
declare const nn: N;
const b4: B = nn.n('x');
export { b1, b2, b3, b4 };
