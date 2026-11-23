// An error in an object literal where a later spread replaces a written property: decided by the literal's type's property, the written value's type named where it fails too (elaborateElementwise).
type Client<D> = { [P in keyof D]: () => void };
type Full = { a: Pick<{ x: () => void; y: () => void }, "x" | "y">; b: { n: number }; c: string };
declare function mkA(): Client<any>;
declare function mkB(): { n: string };
function f(g: Partial<Full> = {}): Full {
  return { a: mkA(), b: mkB(), c: "s", ...g };
}
function h(g: { b: { n: boolean } }): Full {
  return { a: { x() {}, y() {} }, b: mkB(), c: "s", ...g };
}
function k(g: { c?: number }): Full {
  return { a: { x() {}, y() {} }, b: { n: 1 }, c: "s", ...g };
}
