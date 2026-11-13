export {};
type F = { template: string };
type Q = { x?: F; [s: string]: F };
function g(q: { y?: F; [s: string]: F }) {
	const a4: { x?: F; [s: string]: F } = q;
}
interface I { z?: number; [s: string]: number }
type M<K extends string> = { [P in K]?: F };
declare const m: M<"a">;
const b: boolean = m;
function h<K extends string>(m2: M<K>, m3: { readonly [P in K]-?: F }) { const b2: boolean = m2; const b3: boolean = m3; }
