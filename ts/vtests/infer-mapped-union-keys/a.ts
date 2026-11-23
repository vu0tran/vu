// a mapped type over a union of keys, keyof A | M[keyof M]: A inferred from keyof A as a
// homomorphic mapped type, through a conditional template (inferToMappedType over the
// constraint's members; xstate's setup actors)
type Values<T> = T[keyof T];
declare function setup<A extends Record<string, unknown> = {}, M extends Record<string, string> = {}>(o: {
  actors?: { [K in keyof A | Values<M>]: K extends keyof A ? A[K] : never };
  guards?: { [K in keyof A]: (x: { n: number }) => boolean };
}): [A, M];
const r = setup({ actors: { sub: 1, b: 'x' } });
const n: string = r;
const r2 = setup({ actors: { sub: true }, guards: { sub: ({ n }) => n > 1 } });
const n2: string = r2;
const r3 = setup({ guards: { g: ({ n }) => n > 1 } });
const n3: string = r3;
