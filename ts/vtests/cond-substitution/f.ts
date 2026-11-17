export {};
type Ref<T = any> = { value: T };
type IfAny<T, Y, N> = 0 extends 1 & T ? Y : N;
type ShallowRef<T = any> = Ref<T> & { __s: true };
declare function sr1<T>(value: T): T extends Ref ? IfAny<T, ShallowRef<T>, T> : ShallowRef<T>;
declare function sr2<T>(value: T): T extends Ref ? T : ShallowRef<T>;
declare function sr3<T>(value: T): Ref extends T ? ShallowRef<T> : ShallowRef<T>;
export function f<T>(v: T) {
	const a = sr1(v); const n1: number = a.value;
	const b = sr2(v); const n2: number = b.value;
	const c = sr3(v); const n3: number = c.value;
}
