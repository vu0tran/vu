// inferring a rest tuple from parameters ending in a rest of a union of tuples: a union of tuples
type Arg = string | Uint8Array;
declare const cmd: {
  parse: (this: void, p: number, ...[a, b]: [param: Arg, value: Arg] | [config: Record<string, Arg>]) => void;
};
declare const p: Parameters<typeof cmd.parse>;
export const r2: number = p;
type Tail<F> = F extends (...args: [infer H, ...infer T]) => void ? T : never;
declare const t: Tail<typeof cmd.parse>;
export const r3: number = t;
