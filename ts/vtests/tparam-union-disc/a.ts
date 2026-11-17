export {};
interface A { name: string; options?: A[]; d?: { s?: number } }
interface B { name: string; displayName: string; options?: A[]; d?: { s?: number } }
function f<T extends A | B>(prop: T): T {
	if (!prop.options) return prop;
	const options: A[] = [];
	const q: number = prop;
	return true ? { ...prop, options } : prop;
}
