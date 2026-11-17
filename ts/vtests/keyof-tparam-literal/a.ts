// a literal in a tuple contextually typed by type parameters constrained to keyof: it stays a literal
interface TD { a: number }
interface R { resultData: { runData: { [k: string]: TD[] } }; x?: string }
declare function get<TObject extends object, TKey1 extends keyof TObject, TKey2 extends keyof TObject[TKey1]>(object: TObject, path: [TKey1, TKey2]): TObject[TKey1][TKey2];
declare function get<TObject extends object, TKey1 extends keyof TObject>(object: TObject, path: [TKey1]): TObject[TKey1];
declare function get(object: any, path: string[], defaultValue?: any): any;
declare function pick<T, K extends keyof T>(o: T, ks: K[]): Pick<T, K>;
export function f(r: R) {
  const t3 = get(r, ['resultData', 'runData']);
  const n3: [boolean] = [t3];
  const t4 = get(r, ['resultData']);
  const n4: [boolean] = [t4];
  const p = pick(r, ['x']);
  const n5: [boolean] = [p];
}
