// An index signature's length as tsc counts it (the key type, the value type, the name and 4):
// it decides where a long type starts eliding
declare const a: { status: "aaaaaaaaaaaaaa" | "bbbbbbbbbbbbbbbbb"; stamp?: string; results: { [k: string]: { status: string; root_cause?: string; confidence?: string } }; groups?: { id: string; name: string }[]; board_groups?: { a: string; b: number }; tail: number };
const n1: number = a;
declare const b: { [keyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy: string]: { status: string; root_cause?: string; confidence?: string }; [n: number]: { first: string; second: string; third: string }; x1: string; x2: string; x3: string; x4: string; x5: string; x6: string };
const n2: number = b;
declare const c: { [x: symbol]: { status: string; root_cause?: string; confidence?: string; another: string; yetAnother: string }; p1: string; p2: string; p3: string; p4: string; p5: string; p6: string };
const n3: number = c;
