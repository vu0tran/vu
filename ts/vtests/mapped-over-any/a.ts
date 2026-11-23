// A homomorphic mapped type over a type variable instantiated to any (connect's Client<any>): a string index signature, no named properties.
type Client0<D> = { [P in keyof D]: () => void };
type C2<D> = { [P in keyof D]: D[P] extends string ? () => void : never };
declare function mkA(): Client0<any>;
declare function mkB(): C2<any>;
const z: number = mkA();
const z2: number = mkB();
const w: { x: () => void } = mkB();
const r: { x: () => void } = {} as Record<string, () => void>;
const v0: Pick<{ x: () => void; y: () => void }, "x" | "y"> = mkA();
const w0: { x: () => void } = mkA();
