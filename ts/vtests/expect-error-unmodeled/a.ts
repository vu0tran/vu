export {};
type H = { a: Array<(x: number) => void>; b: Array<(s: string) => void> };
class C {
	h: H = { a: [], b: [] };
	add<K extends keyof H>(k: K, ...fs: Array<H[K][number]>) {
		// @ts-expect-error FIX
		this.h[k].push(...fs);
	}
	q<K extends keyof H>(k: K) {
		// @ts-expect-error unused
		const z = 1;
	}
}
const n: number = 'x';
