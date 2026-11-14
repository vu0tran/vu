export {};
type P<T> = { [K in keyof T]?: T[K] };
const a: P<{ [k: string]: number }> = { z: undefined };
declare const b: P<{ [k: string]: number }>;
const c: number = b.q;
type R<T> = { [K in keyof T]-?: T[K] };
declare const d: R<{ [k: string]: number | undefined }>;
const e: number = d.q;
