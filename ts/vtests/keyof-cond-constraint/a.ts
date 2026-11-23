// S to keyof of a conditional type whose constraint is generic (Exclude<L, Error>): S to keyof of that constraint.
type Compat<P, S> = { [K in keyof P]-?: Awaited<P[K]> extends S ? K : never }[keyof P] & string;
type Pick1<P, S, N> = N extends keyof P ? N : keyof P;
declare function expose<P, S, N extends Compat<P, S>>(name: N): void;
declare function expose2<P>(name: keyof P): void;

function f<L, Q extends { id: string }>() {
  const a: keyof Exclude<L, Error> = "id";
  const b: keyof Exclude<Q, Error> = "id";
  const c: Compat<Exclude<L, Error>, string> = "id";
  const d: keyof Extract<L, object> = "id";
  const e: keyof Exclude<L, Error> = "id" as keyof L;
  expose2<Exclude<L, Error>>("id");
  expose<Exclude<L, Error>, string, "id">("id");
  const g: Pick1<Exclude<L, Error>, string, Compat<Exclude<L, Error>, string>> = "id";
}
function f2<L extends { id: string; n: number }>() {
  const a: keyof Exclude<L, Error> = "id";
  const d: keyof Exclude<L, Error> = "zz";
  const k: keyof Exclude<L, Error> = "id" as keyof L;
}
