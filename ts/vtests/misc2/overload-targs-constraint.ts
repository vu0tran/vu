type Aw<T> = T | PromiseLike<T>;
interface EFR<T extends any[]> {
  (name: string | Function, fn: (...args: T) => Aw<void>, options?: number): void;
  (name: string | Function, options: { a?: number }, fn: (...args: T) => Aw<void>): void;
}
interface TEF {
  <T extends any[] | [any]>(cases: ReadonlyArray<T>): EFR<T>;
  <T extends ReadonlyArray<any>>(cases: ReadonlyArray<T>): EFR<T extends readonly [...infer A] ? A : never>;
  <T>(cases: ReadonlyArray<T>): EFR<T[]>;
}
declare const each: TEF;
type Tg = { scope: 'c'; x: {} } | { scope: 'i'; y: string[] };
declare function use(t: Tg): void;
each<Tg>([{ scope: 'c', x: {} }])('n', (target) => { use(target); });
declare function ov<T extends string>(x: T): 1;
declare function ov<T>(x: T): 2;
export const o1: 2 = ov<number>(1);
export const o2: 1 = ov<'a'>('a');
