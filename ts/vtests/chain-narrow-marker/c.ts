export {};
interface NI { type: string; version: string; opt?: { z: number }; u: { z: number } | undefined }
interface GN { instance: NI }
declare const nodes: Map<string, GN>;
const g = nodes.get("a");
if (g?.instance.type === "s") { const q: number = g.instance.type; }
if (g?.instance.type !== "s") { const v = g?.instance.version; const w: number = v; } else { const x: number = g.instance.version; }
if (g?.instance.opt?.z === 1) { const y: string = g.instance.opt.z; }
if (g?.instance.u !== undefined) { const y2: string = g.instance.u.z; }
const g2 = nodes.get("b");
if (g2?.instance.type !== "t") { const q2 = g2?.instance.opt.z; }
