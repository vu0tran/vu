// declared and inferred predicates choosing filter's overload; discriminants of a narrowed union member
export {};
interface Prop { type: "Property"; key: string; value: number }
interface Spread { type: "Spread"; arg: string }
declare const props: (Prop | Spread)[];
const r = props.filter((p) => p.type === "Property").map(({ key, value }) => [key, value]);
const n: number = r;



const r2 = props.filter((p): p is Prop => p.type === "Property");
const n2: number = r2;
const isP = (p: Prop | Spread) => p.type === "Property";
const m: number = isP;
