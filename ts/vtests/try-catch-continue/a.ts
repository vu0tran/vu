// A catch block that continues or breaks doesn't reach what follows the try statement.
declare function get(): string[];
declare function use(x: string[]): void;
export function f(xs: number[]) {
	for (const x of xs) {
		let p;
		try {
			p = get();
		} catch {
			continue;
		}
		use(p);
	}
	let q;
	try { q = get(); } catch { return; }
	use(q);
	let r: string[] | undefined;
	try { r = get(); } catch { return; }
	use(r);
}
