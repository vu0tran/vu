// A unique symbol is a unit type: === and !== narrow by it; unions print it after boolean.
const EVALUATING = Symbol('evaluating');
const OTHER = Symbol('other');
declare const cached: boolean | typeof EVALUATING | typeof OTHER | undefined;
export function f(): boolean {
	if (cached !== undefined) return cached === EVALUATING ? false : cached;
	return true;
}
export function g(): typeof EVALUATING | undefined {
	if (cached === EVALUATING) { const s: typeof EVALUATING = cached; return s; }
	return undefined;
}
declare const u: unknown;
export const h: typeof OTHER | 1 = u === OTHER ? u : 1;
interface D2 { a: 1; [OTHER]: 3 }
declare const kd2: keyof D2;
export const o8: boolean = kd2;
