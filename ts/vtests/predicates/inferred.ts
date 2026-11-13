// type predicates inferred from function bodies (getTypePredicateFromBody)
export {};
declare const xs: (string | undefined)[];
declare const os: ({ a: 1 } | undefined | null)[];
declare const ns: (number | string)[];
const r1 = xs.filter((x) => x !== undefined);
const n1: number = r1;
const r2 = xs.filter((x) => !!x);
const n2: number = r2;
const r3 = os.filter((o) => !!o);
const n3: number = r3;
const r4 = ns.filter((v) => typeof v === "string");
const n4: number = r4;
const f5 = (v: number | string) => typeof v === "number";
const n5: number = f5;
function f6(v: number | string, w: Date | undefined) { return w !== undefined; }
const n6: number = f6;
function f7(v: number | string) { if (v === 1) return true; return typeof v === "number"; }
const n7: number = f7;
const f8 = 1;
const n8: number = f8;
const f9 = (x: number) => x > 0;
const n9: number = f9;
const f10 = (x: Date | string) => x instanceof Date;
const n10: number = f10;
const r11 = ns.find((v) => typeof v === "number");
const n11: number = r11;
class K { isS(v: number | string) { return typeof v === "string"; } }
const n12: number = new K().isS;
const f13 = (x: boolean | string) => typeof x === "string";
const n13: number = f13;
const f14 = (x: string | number) => { x = 1; return typeof x === "number"; };
const n14: number = f14;
const f15 = (x: string | number, y: boolean) => typeof x === "number" && y;
const n15: number = f15;
const f16 = (x: "a" | "b" | 1) => x === "a" || x === "b";
const n16: number = f16;
const f17 = function (x: string | null) { return x != null; };
const n17: number = f17;
const o18 = { m(x: string | null) { return x !== null; } };
const n18: number = o18.m;
const f19 = async (x: string | null) => x !== null;
const n19: number = f19;
const f20 = (x: string | null) => (x !== null);
const n20: number = f20;
