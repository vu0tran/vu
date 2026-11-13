// switch on a discriminant (x.kind, x?.kind), defaults with labels, the flow after a switch
export {};
type K = "a" | "b" | "c" | "d";
declare const v: string;
function h1(k: K) {
	switch (k) { case "a": { const n: number = k; break; } case "b": default: { const n: number = k; break; } case "c": return; }
	const n: number = k;
}
function h2(k: string) {
	switch (k) { case "P": break; case "PP": default: { const n: number = k; break; } }
	const n: number = k;
}
function h3(k: K) {
	switch (k) { case v: { const n: number = k; break; } default: { const n: number = k; } }
}
type A = { type: "a"; pa: number };
type B = { type: "b"; pb: string };
type Cc = { type: "c"; pc: boolean };
function h4(x: A | B | Cc) {
	switch (x.type) { case "a": return; case "b": default: { const n: number = x; } }
	const n: number = x;
}
function h5(x: A | B | Cc | undefined) {
	switch (x?.type) { case "a": return; default: { const n: number = x; } }
	const n: number = x;
}
