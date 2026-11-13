// an element access with a never key
export {};
interface P { [key: string]: V }
interface RL { __rl: true; mode: string; value: string }
interface FV { options: string; combinator: "and" }
type V = string | number | P | RL | FV | null | P[];
declare const pv: V;
declare const k: string;
function f(pv: V) {
	if (typeof pv !== 'object') return;
	if (Array.isArray(pv)) return;
	const x = pv![k as keyof typeof pv];
	const n: number = x;
	const y: keyof typeof pv = "a";
}
