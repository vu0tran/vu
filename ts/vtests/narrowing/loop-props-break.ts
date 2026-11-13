// properties not narrowed before a loop with breaks: their declared type after it
export {};
declare const ks: string[];
declare function r(k: string): string | undefined;
function f(item: { m?: string; n: number | string }) {
	for (const k of ks) {
		const v = r(k);
		if (v) { item.m = v; break; }
	}
	const a: number = item.m;
	while (Math.random()) { item.n = 1; if (item.n) break; }
	const b: boolean = item.n;
}
