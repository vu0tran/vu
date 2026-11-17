export {};
interface A { k: 'a'; options?: A[] }
interface B { k: 'b'; displayName: string; options?: A[] }
function f<T extends A | B>(p: T): T {
	if (p.k === 'a') return p;
	return p;
}
function g<T extends A | B>(p: T): T {
	if (p.k === 'a') { const z: number = p; }
	return p;
}
function h(p: A | B) {
	if (!p.options) { const z: number = p; }
}
