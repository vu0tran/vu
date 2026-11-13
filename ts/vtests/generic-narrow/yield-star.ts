function* ya() { yield 1; return "r"; }
function* yb() { const r = yield* ya(); yield* [true, false]; yield* new Set(["x"]); return r; }
const g: boolean = yb();
function* yc(): Generator<number, void, unknown> { yield* ya(); yield* [1, 2]; }
for (const x of yb()) { const y: boolean = x; }
export {};
