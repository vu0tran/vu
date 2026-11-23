// a property a later spread may replace (its type: the written value's or the spread's), with an
// object literal value: elaborated into with that type, else the error is on the property with
// the value's own type; a replaced shorthand is related with the property's type
export {};
type Rec = { id: string; input: { a: number }; config: { v: string; t: number; need: number }; tags: string[] };
const input = { a: 1 };
function rec(o: Partial<Rec> = {}): Rec {
  return { id: "x", input, config: { v: "p", t: 0 }, tags: [], ...o };
}
function rec2(o: Partial<Rec> = {}): Rec {
  return { id: "x", input, config: { v: "p", t: 0, need: "n" }, tags: [], ...o };
}
