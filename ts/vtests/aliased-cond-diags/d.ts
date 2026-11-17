export {};
interface N { type: string }
interface H { nodes: N[] }
interface W { nodes: N[]; activeVersion?: H | null }
export function f(w: W, p: boolean) {
	const s = (p && w.activeVersion ? w.activeVersion.nodes : w.nodes).find((n) => n.type === 'x');
	if (s) { const q = s.type; }
}
