// an object literal where a later spread may replace properties with object values, none of them
// failing, but the literal missing a required property: tsc's error is on the whole literal
export {};
type Rec = { id: string; config: { v: string }; tags: string[]; need: number };
function rec(o: Partial<Omit<Rec, 'need'>> = {}): Rec {
  return { id: "x", config: { v: "p" }, tags: [], ...o };
}
