// a union written with a named union in it, instantiated: the origin's members are, so the name stays
// (React's ReactElement<any, string | JSXElementConstructor<any>>)
type JC<P> = ((props: P) => string) | (new (props: P) => { x: 1 });
interface R3<P = any, T = string | JC<P>> { type: T }
declare const r3: R3;
const q5: number = r3;
declare function f<P>(p: P): string | JC<P> | undefined;
const v6 = f(1);
const q6: typeof v6 = true;
