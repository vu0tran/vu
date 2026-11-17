export {};
interface A { name: string; options?: A[] }
interface B { name: string; displayName: string; options?: A[] }
function f<T extends A | B>(prop: T): T {
	if (!prop.options) return prop;
	return prop;
}
function g<T extends A | B>(prop: T): T {
	if (!prop.options) { const z: number = prop; }
	return prop;
}
function h<T extends A | B>(prop: T): T {
	return prop;
}
