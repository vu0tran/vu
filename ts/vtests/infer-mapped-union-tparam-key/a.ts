// (inference to Record<"expanded" | R, X>, R being inferred: a type parameter member of the
// mapped type's key union gets the source's keys, as a lone one would, inferToMappedType)
type CSS = { color?: string; marginBottom?: string };
declare function makeStyles<P, S extends string = never>(): <R extends string>(f: (p: P, classes: Record<S, string>) => Record<S | R, CSS>) => () => { classes: Record<S | R, string> };
const useS = makeStyles<void, "expanded">()(() => ({ alert: { color: "x" }, expanded: {}, b4: { marginBottom: "4px" } }));
const cls = useS().classes;
const n: number = cls;
declare function rec<K extends string>(r: Record<"fixed" | K, number>): K;
const k = rec({ fixed: 1, a: 2, b: 3 });
const n2: number = k;
export {};
