// a template literal type inferred to another: its parts matched to the target's holes (inferFromLiteralPartsToTemplateLiteral)
declare function f<P extends string>(p: `/${P}`): P;
declare const s: `/internal/api/${string}`;
export const a: number = f(s);
type G<T> = T extends `${infer A}.${infer B}` ? [A, B] : 0;
export const b: number = null! as G<`x.${string}.z`>;
export const c: number = null! as G<`${string}y`>;
export const d: number = null! as G<`a${number}.b`>;
type H<T> = T extends `pre${infer R}` ? R : 0;
export const e: number = null! as H<`pre${string}post`>;
export const g: number = null! as H<`no${string}`>;
