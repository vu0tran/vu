// variables without a type (let x;) through loops, for-of over them, for-in keys indexing arrays
export {};
declare const xs: number[];
function f1() {
	let a;
	for (const x of xs) { a = x; }
	const n: string = a;
}
function f2() {
	let a;
	for (const x of xs) { const q: string = a; a = "s"; }
}
function f3() {
	let a;
	while (Math.random()) { if (a) break; a = 1; }
	const n: string = a;
}
function f4() {
	let a = undefined;
	for (let i = 0; i < 3; i++) { a = i > 1 ? "x" : 1; }
	const n: boolean = a;
}
function f5() {
	let a;
	for (const x of xs) { a = a ? a + x : x; }
	const n: string = a;
}
