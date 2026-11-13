// switch on a discriminant (x.kind, x?.kind), defaults with labels, the flow after a switch
export {};
type K = "a" | "b" | "c";
function h1(k: K) {
	switch (k) { case "a": break; case "b": break; case "c": break; }
	const n: number = k;
}
function h2(k: K) {
	switch (k) { case "a": break; default: break; }
	const n: number = k;
}
function h3(k: K) {
	switch (k) { case "a": return; default: break; }
	const n: number = k;
}
function h4(k: K, q: K) {
	switch (k) { case "a": if (q === "a") return; break; default: return; }
	const n: number = k;
	const m: number = q;
}
type A = { type: "a"; pa: number };
type B = { type: "b"; pb: string };
type AB = A | B;
function h5(x: AB) {
	switch (x.type) { case "a": break; case "b": break; }
	const n: number = x;
}
function h6(x: AB | undefined) {
	switch (x?.type) { case "a": break; case "b": break; }
	const n: number = x;
}
function h7(k: string) {
	switch (k) { case "a": break; case "b": return; }
	const n: number = k;
}
function h8(k: K) {
	switch (k) { case "a": k = "b"; break; case "b": break; }
	const n: number = k;
}
