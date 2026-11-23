// Inference to a mapped type over a union of keys, { [K in keyof T | Values<M>]: ... } (xstate's
// setup): inferToMappedType over each member, keyof T a homomorphic mapped type (T from the
// reverse mapped type); Values<M> (M[keyof M]) infers nothing.
type Values<T> = T[keyof T];
declare function setup<T extends Record<string, { run(): unknown }> = {}, M extends Record<string, string> = {}>(x: {
  actors?: { [K in keyof T | Values<M>]: K extends keyof T ? T[K] : never };
  map?: M;
}): { actors: T; map: M };
const offer = { run: () => 1 };
const s = setup({ actors: { offer } });
const n1: number = s;
const n2: string = s.actors.offer.run();
declare function homo<T>(x: { [K in keyof T | 'x']: K extends keyof T ? T[K][] : never }): T;
const h: number = homo({ a: [1], x: [] });
