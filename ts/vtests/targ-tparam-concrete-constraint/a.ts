// (a type parameter alone as a type argument against a concrete constraint: decided by its own
// constraint, unknown without one)
type Vars = { [key: string]: any };
type Q<V extends Vars> = { variables: V };
type N<V extends number> = { n: V };
type O<V extends object> = { o: V };
function f1<T>(x: Q<T>) { return x; }
function f2<T extends string>(x: N<T>) { return x; }
function f3<T extends { a: 1 }>(x: O<T>, y: Q<T>) { return [x, y]; }
function f4<T extends Vars>(x: Q<T>) { return x; }
const n: number = f4;
export {};
