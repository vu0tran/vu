export {};
type Ref<T = any> = { value: T };
type IfAny<T, Y, N> = 0 extends 1 & T ? Y : N;
type ShallowRef<T = any> = Ref<T> & { __s: true };
export function f2<T>(s: T extends Ref ? IfAny<T, ShallowRef<T>, T> : ShallowRef<T>, v: T) { s.value = v; }
export function f4<T>(s: Ref extends T ? ShallowRef<T> : ShallowRef<T>, v: T) { s.value = v; const n: number = s.value; }
export function f5<T>(s: Ref extends T ? T extends Ref ? IfAny<T, ShallowRef<T>, T> : ShallowRef<T> : ShallowRef<T>, v: T) { const n: number = s.value; }
