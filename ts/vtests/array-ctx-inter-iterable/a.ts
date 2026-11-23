declare const it: (Iterable<string> & { tag: 1 }) | number;
const arr: typeof it = ['a', 'b'];
type Node = string | number | (Iterable<Node> & { kind: 'el' });
const n: Node = ['a', 1];
const z: number = n;
export {};
