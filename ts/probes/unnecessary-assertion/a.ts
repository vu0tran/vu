interface D { a: number; f(): void }
declare function k<T>(): T;
declare function use(d: D): void;
export const v1 = k() as D;
use(k() as D);
export function f1() { return k() as D; }
export const v3 = (k() as D)['a'];
declare function id<T>(x: T): T;
declare const d: D;
export const r2 = id(d) as D;
export const r4 = k<D>() as D;
declare function plain(): D;
export const r6 = plain() as D;
declare const s: string;
export const w = s as string;
declare const row: HTMLTableRowElement;
export const k2 = row.querySelector('td.label') as HTMLElement | null;
declare const maybe: string | undefined;
export const n1: string | undefined = maybe!;
export const n2 = { key: maybe! };
declare function take(x: string | undefined): void;
take(maybe!);
const items = [1, 2].map((i) => ({ id: i, label: String(i) as string | undefined }));
export { items };
