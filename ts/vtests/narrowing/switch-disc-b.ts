// switch on a discriminant (x.kind, x?.kind), defaults with labels, the flow after a switch
export {};
type A = { type: "a"; pa: number };
type B = { type: "b"; pb: string };
type Cc = { type: "c"; pc: boolean };
function g1(x: A | B | Cc) {
	switch (x.type) { case "a": return; case "b": break; }
	const n: number = x;
}
function g2(x: A | B | Cc) {
	switch (x.type) { case "a": x.pa; break; case "b": { const n: number = x; } }
}
function g3(x: A | B | Cc) {
	switch (x.type) { case "a": return; default: { const n: number = x; } }
}
function g4(x: A | B | Cc) {
	switch (x.type) { case "a": case "c": { const n: number = x; break; } default: { const n: number = x; } }
	const m: number = x;
}
function g5(o: { x: A | B }) {
	switch (o.x.type) { case "a": { const n: number = o.x; } }
}
function g6(x: A | B | Cc) {
	switch (x.type) { case "a": { const n: number = x; } }
	const m: number = x;
}
function g7(x: A | B | undefined) {
	switch (x?.type) { case undefined: { const n: number = x; break; } case "a": { const n: number = x; } }
}
function g8(x: A | B | Cc) {
	switch (x.type) { default: { const n: number = x; break; } case "a": { const n: number = x; } }
}
function g9(x: A | B | Cc) {
	switch (x.type) { case "a": return; case "b": return; }
	const n: number = x;
}
