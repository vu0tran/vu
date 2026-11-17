export {};
type H = { a: Array<(x: number) => void>; b: Array<(s: string) => void> };
declare const h: H;
export function run<K extends keyof H>(k: K) {
	for (const f of h[k]) { const n: number = f; }
}
