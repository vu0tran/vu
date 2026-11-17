export {};
interface NJ { name?: string; id: string }
declare function ser(k: string): NJ | undefined;
declare function conns(n: string | undefined): { a: 1 } | undefined;
export const p = {
  serialize(m: Map<string, number>): NJ[] {
    const nodes: NJ[] = [];
    const connections: Record<string, { a: 1 }> = {};
    for (const [k, v] of m) {
      const s = ser(k);
      if (!s) continue;
      nodes.push(s);
      const nodeName = s.name;
      const nc = conns(nodeName);
      if (nc && nodeName !== undefined) {
        connections[nodeName] = nc;
      }
    }
    return nodes;
  },
};
