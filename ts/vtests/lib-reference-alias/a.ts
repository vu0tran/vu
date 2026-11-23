/// <reference lib="esnext.float16" />
// A lib name TypeScript maps to a file of another name (@types/node references esnext.float16,
// which is lib.es2025.float16.d.ts).
declare const f: Float16Array;
type U = Uint8Array | Float16Array;
declare const u: U;
const n1: number = f;
const n2: number = u;
const n3: string = Math.f16round(1);
export {};
