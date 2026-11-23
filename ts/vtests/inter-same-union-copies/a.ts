// identical() comparing two instantiations of one anonymous object type structurally, through the
// intersection-size check: A & A & A of one union made three times is A.
type Code = 100 | 101 | 200 | 201 | 202 | 300 | 301 | 400 | 401 | 404 | 500 | 502;
type Ep<S> = { input: {}; output: {}; status: S };
type Eps<C> = C extends any ? Ep<C> : never;
type U1 = Eps<Code>;
type I = U1 & Eps<Code> & Eps<Code>;
declare const i: I;
const n: number = i;
