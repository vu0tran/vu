interface S { _zod: { optin: "optional" | undefined; input: unknown } }
interface Str extends S { _zod: { optin: undefined; input: string } }
interface Num extends S { _zod: { optin: undefined; input: number } }
type In<T extends S> = T["_zod"]["input"];
type NoOpt<T extends readonly S[]> = { [k in keyof T]: T[k] extends S ? In<T[k]> : never };
export const c1: number = null! as NoOpt<[Str, Num]>;
type W1<T extends readonly S[]> = T extends readonly [...infer P extends S[], infer Tl extends S] ? [P, Tl] : 0;
export const c2: number = null! as W1<[Str, Num]>;
type Sp<T extends readonly unknown[], R> = [...T, ...(R extends S ? R[] : [])];
export const c3: number = null! as Sp<[1, 2], null>;
export const c4: number = null! as Sp<NoOpt<[Str, Num]>, null>;
