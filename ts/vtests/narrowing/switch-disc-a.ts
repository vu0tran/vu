// switch on a discriminant (x.kind, x?.kind), defaults with labels, the flow after a switch
export {};
type A = { type: "a"; pa: number };
type B = { type: "b"; pb: string };
function f1(x?: A | B | null) {
	switch (x?.type) { case "a": { const n: string = x.pa; break; } case "b": { const n: number = x.pb; } }
}
function f2(x: A | B) {
	switch (x.type) { case "a": { const n: string = x.pa; break; } default: { const n: number = x.pb; } }
}
function f3(x?: A | B | null) {
	if (x?.type === "a") { const n: string = x.pa; }
}
function f4(x?: A | B | null) {
	switch (x?.type) { case "a": case "b": { const n: number = x; break; } default: { const m: number = x; } }
}
enum E { A = "a", B = "b" }
type C = { type: E.A; pa: number };
type D = { type: E.B; pb: string };
function f5(x?: C | D | null) {
	switch (x?.type) { case E.A: { const n: string = x.pa; break; } }
}
