// Two generic mapped types with as clauses (hono's MergeSchemaPath): related only when their name types are the same, the source's key as the target's (mappedTypeRelatedTo).
type MergePath<A extends string, B extends string> = B extends "" ? A : `${A}/${B}`;
type MSP<S, P extends string> = { [K in keyof S & string as MergePath<P, K>]: S[K] };
type Plain<S> = { [K in keyof S]: S[K] };
function f<S, T, P extends string, Q extends string>(a: MSP<S, P>, b: MSP<S, P>, c: Plain<S>) {
  const x: MSP<S, Q> = a;
  const y: MSP<S, P> = b;
  const z: Plain<S> = a;
}
