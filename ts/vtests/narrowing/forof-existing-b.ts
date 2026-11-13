// for-of over an existing variable: narrowing in the body and after the loop
export {};
function f(xs: ("a" | "b")[], ys: number[]) {
	let v: "a" | "b" | "c" = "c";
	for (v of xs) { if (v === "a") break; const m: number = v; }
	const n: number = v;
	let w: number | string = "s";
	for (w of ys) { const q: number = w; }
	const p: number = w;
	let u: string | undefined;
	for (u in {}) { }
	const r: number = u;
}
