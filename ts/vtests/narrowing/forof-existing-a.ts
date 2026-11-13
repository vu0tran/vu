// for (x of xs) / for (x in o) over a variable declared before
export {};
declare const o: { [k: string]: { [k: string]: number[] } };
function f() {
	let a: string;
	let b: string;
	let n: number | undefined;
	for (a of Object.keys(o)) {
		for (b of Object.keys(o[a])) {
			const q: string = o[a][b];
		}
	}
	let x: string | number = 1;
	const k0: number = x;
	for (x in o) { const m: number = x; }
	const k1: number = x;
	let y: string = "a";
	for (y of ["b", "c"]) { const m: number = y; }
	var z: number;
	for (z of [1, 2]) { z.toFixed(); }
}
