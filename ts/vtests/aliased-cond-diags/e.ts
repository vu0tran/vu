export {};
interface N { type: string }
interface H { nodes: N[] }
interface W { nodes: N[]; activeVersion?: H | null }
declare function isX(n: N): boolean;
export function f1(w: W, p: boolean) {
	const s = (w.activeVersion ? w.activeVersion.nodes : w.nodes).find((n) => n.type === 'x');
	if (s) { const q = s.type; }
}
export function f2(w: W, p: boolean) {
	const s = (p && w.activeVersion ? w.activeVersion.nodes : w.nodes).find(isX);
	if (s) { const q = s.type; }
}
export function f3(w: W, p: boolean) {
	const s = (p && w.activeVersion ? w.activeVersion.nodes : w.nodes)[0];
	if (s) { const q = s.type; }
}
export function f4(w: W, p: boolean) {
	const s = p && w.activeVersion ? w.activeVersion.nodes : w.nodes;
	if (s) { const q = s; }
}
