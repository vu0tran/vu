// for await over a type whose [Symbol.asyncIterator]() returns any: any elements
declare const s: { [Symbol.asyncIterator](): any };
export async function f() {
  for await (const x of s) { const n: number = x; const k: string = 1; }
}
