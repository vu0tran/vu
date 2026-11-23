// (a callback's object literal returns for an unconstrained T, useMemo's: widened as without a
// context, each given the others' properties as optional undefined)
declare function useMemo<T>(f: () => T, deps: unknown[]): T;
declare const flag: boolean;
const d = useMemo(() => {
  if (flag) {
    return { a: 1, p: "x" as string | undefined };
  }
  return { a: 2 };
}, []);
const s: string = d.p;
const f2 = () => {
  if (flag) return { a: 1, p: "x" };
  return { a: 2 };
};
const s2: number = f2().p;
const d2 = useMemo(() => (flag ? { k: "a" } : { k: "b", z: 1 }), []);
const s3: string = d2.z;
const d3 = useMemo(() => "lit", []);
const s4: number = d3;
declare function useK<T extends "a" | "b">(f: () => T): T;
const d4 = useK(() => (flag ? "a" : "b"));
const s5: number = d4;
export {};
