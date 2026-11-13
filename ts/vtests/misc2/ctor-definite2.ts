export const enum St { Eq = 'equal' }
type Node = { id: string };
export class CS<T extends Node> {
  readonly nodes: Map<string, { node: T; status: St }>;
  readonly conns: { a: {} };
  constructor(from: T[], to: T[]) {
    if (from === to) {
      this.nodes = new Map(from.map((node) => [node.id, { node, status: St.Eq }]));
      this.conns = { a: {} };
    } else {
      this.nodes = new Map();
      this.conns = { a: {} };
    }
  }
}
