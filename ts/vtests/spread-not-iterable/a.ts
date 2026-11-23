// a spread in an array literal of a type that isn't iterable (a member, or the whole): TS2488, its
// elements any
declare const RESET: unique symbol;
type SetStateActionWithReset<Value> = Value | typeof RESET | ((prev: Value) => Value | typeof RESET);
interface AsyncStorage<Value> {
  getItem: (key: string, initialValue: Value) => PromiseLike<Value>;
  setItem: (key: string, newValue: Value) => PromiseLike<void>;
}
interface SyncStorage<Value> {
  getItem: (key: string, initialValue: Value) => Value;
  setItem: (key: string, newValue: Value) => void;
}
interface WritableAtom<Value, Args extends unknown[], Result> { read: Value; write: (...args: Args) => Result }
declare function atomWithStorage<Value>(key: string, initialValue: Value, storage: AsyncStorage<Value>, options?: { getOnInit?: boolean }): WritableAtom<Value | Promise<Value>, [SetStateActionWithReset<Value | Promise<Value>>], Promise<void>>;
declare function atomWithStorage<Value>(key: string, initialValue: Value, storage?: SyncStorage<Value>, options?: { getOnInit?: boolean }): WritableAtom<Value, [SetStateActionWithReset<Value>], void>;
declare const getStorage: any;
declare function useAtom<V, A extends unknown[], R>(a: WritableAtom<V, A, R>): [V, (...args: A) => R];
interface Opt { token: string }
const at = atomWithStorage<Opt[]>('k', [], getStorage<Opt[]>(), { getOnInit: true });
export function f(o: Opt) {
  const [sel, setSel] = useAtom(at);
  setSel((prev) => [...prev, o]);
  setSel((prev) => {
    const r = [...prev, o];
    const q: number = r;
    return r;
  });
  const p = Promise.resolve(1);
  const s = [...p, 1];
  const s2: number = s;
  const u = [...(Math.random() ? [1] : { a: 1 })];
  const u2: number = u;
}
