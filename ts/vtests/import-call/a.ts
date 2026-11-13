// import("m"): a promise of the module namespace
export {};
async function g() {
	const m = await import('./m');
	const n: string = m.a;
	const k = new m.K();
	const q: string = k.v;
	const z: string = m.default;
	const w: number = m;
	const p = import('./m');
	const pp: number = p;
}
