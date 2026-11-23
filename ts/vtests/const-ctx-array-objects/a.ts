// object literals in an array in a const type parameter's context: in a const context by their own
// properties' contextual types (isConstContext through the array's element type)
export {};
type Opts = { template?: string; n?: number };
declare function cmd<const O extends Opts, const N extends string>(def: { name: N; usage?: { options: { [K in keyof O]?: true } }[]; examples?: { description: string; options?: Partial<O> }[]; opts: O }): [O, N];
const r = cmd({ name: "x", opts: { template: "a" }, usage: [{ options: { template: true } }], examples: [{ description: "d", options: { template: "a" } }] });
const s: string = r;
declare function k<const T extends readonly unknown[]>(x: { items: { v: T }[] }): T;
const t = k({ items: [{ v: [1, "a"] }] });
const u: string = t;
