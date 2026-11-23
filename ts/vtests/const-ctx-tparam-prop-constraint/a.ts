// an object literal argument whose property's contextual type is a type parameter that isn't
// const, beside a const one: its properties read through that type parameter's constraint, where
// no const type variable is (isConstContext; getApparentTypeOfContextualType)
interface Opts<T extends readonly unknown[], A, B extends { k: string }> {
  name: string;
  tools?: T;
  app?: A;
  b?: B;
}
declare function init<const T extends readonly unknown[], A = unknown, B extends { k: string } = { k: string }>(o: Opts<T, A, B>): [T, A, B];

const r = init({ name: 'n', app: { id: Math.random(), tag: 'x' }, b: { k: 'y' }, tools: [1, 'a'] });
const t: number = r;
