export {};
type Ref<T = any> = { value: T };
type IfAny<T, Y, N> = 0 extends 1 & T ? Y : N;
type ShallowRef<T = any> = Ref<T> & { __s: true };
declare function shallowRef<T>(value: T): Ref extends T ? T extends Ref ? IfAny<T, ShallowRef<T>, T> : ShallowRef<T> : ShallowRef<T>;
export function f<T>(v: T) {
	const s = shallowRef(v);
	s.value = v;
	const n: number = s.__s;
}
