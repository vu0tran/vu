// T === 'x' (T constrained): T is kept (its constraint narrowed where tsc substitutes it)
type Resolvers = { A: { a: number }; B: { b: string }; C: { c: boolean } };
type GqlTypes = keyof Resolvers;
type RegisterResolverFn = <Name extends GqlTypes>(typeName: Name, resolver: Resolvers[Name]) => void;
declare function reg(r: { resolver: RegisterResolverFn }): void;
let qa: { a: number };
let qb: { b: string };
reg({
  resolver: (typeName, resolverDef) => {
    if (typeName === 'A') {
      const n: string = typeName;
      qa = resolverDef;
    }
    if (typeName === 'B') {
      qb = resolverDef;
    }
  },
});
export const g = <N extends 'x' | 'y' | 'z'>(t: N) => {
  if (t === 'x') { const n: number = t; }
  if (t !== 'x') { const n: number = t; }
};
export const h = <N extends string>(t: N) => {
  if (t === 'x') { const n: number = t; }
  if (t !== 'x') { const n: number = t; }
};
