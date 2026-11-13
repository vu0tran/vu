// discriminants and predicates over intersections and unions of predicate methods
export {};
interface A<T> { check(value: any): value is T; a: 1 }
interface B<T> { check(value: any): value is T; b: 1 }
type Type<T> = A<T> | B<T>;
interface Node { type: string }
interface VD extends Node { kind: "var" | "let" }
declare const n: { VD: Type<VD> };
function f(node: Node) {
	if (n.VD.check(node)) { const k: number = node.kind; }
}
