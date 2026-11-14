export {};
class A {
  x = 1;
  protected p(): void {}
  private q = 2;
  static s = 3;
}
type K = keyof A;
const k: K = "p";
type P<T> = { [Key in keyof T]?: T[Key] };
declare const a: A;
const b: P<A> = a;
const c: P<A> = { x: 1, p: 2 };
