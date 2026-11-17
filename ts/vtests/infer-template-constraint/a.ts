// infer in a template literal span: constraint string, which a failed inference falls back to
type P<S> = S extends `${infer L}['${infer K}']${infer R}` ? [L, K, R] : 'no';
type Q<S> = S extends `${infer L}['${infer K}']` ? [L, K] : 'no';
type E<S> = S extends [infer A extends string] ? A : 'no';
export const a: P<'abc'> = 1;
export const b: P<"x['y']z"> = 1;
export const c: Q<'abc'> = 1;
export const d: P<string> = 1;
export const g: E<[1]> = 1;
export const h: E<['s']> = 1;
