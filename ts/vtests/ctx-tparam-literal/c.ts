export {};
type Exactly<T, X> = T & Record<Exclude<keyof X, keyof T>, never>;
declare function p<T, Mask extends Exactly<{ [k in keyof T]?: true }, Mask>>(t: T, mask: Mask): Mask;
declare function q<T, Mask extends { [k in keyof T]?: true }>(t: T, mask: Mask): Mask;
declare const t: { origin: string; nodeNames: string[] };
const x1: number = p(t, { origin: true });
const x2: number = q(t, { origin: true });
