export {};
interface N { type: string }
interface H { nodes: N[] }
interface W { nodes: N[]; activeVersion?: H | null }
export function f1(w: W) {
	const s = (w.activeVersion ? w.activeVersion.nodes : w.nodes).find((n) => n.type === 'x');
	const t = s;
}
export function f2(w: W) {
	const s = (w.activeVersion ? w.activeVersion.nodes : w.nodes).find((n) => n.type === 'x');
	s;
	if (s) { }
}
export function f3(w: W) {
	const s = (w.activeVersion ? w.activeVersion.nodes : w.nodes).map((n) => n.type === 'x');
	if (s) { }
}
