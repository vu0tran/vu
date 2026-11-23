// A generic mapped type with an as clause (hono's MergeSchemaPath) to an object type: no members of its own, so a string index signature takes its template and a required property fails.
type MP<A extends string, B extends string> = `${A}/${B}`;
type MSP<S, P extends string> = { [K in keyof S & string as MP<P, K>]: S[K] };
type Sch = { [path: string]: { v: number } };
function f<S extends Sch, P extends string>(a: MSP<S, P>) {
  const x: MSP<Sch, string> = a;
  const y: { [k: string]: { v: number } } = a;
  const z: { [k: string]: { w: number } } = a;
  const q: { [k: `x${string}`]: string } = a;
  const r: { a: number } = a;
}
