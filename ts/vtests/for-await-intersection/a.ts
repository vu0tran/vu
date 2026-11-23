// for await over an intersection reads the member that has [Symbol.asyncIterator] (process.stdin's
// ReadStream & { fd: 0 }); an iterator typed any gives any; iterating never is TS2488
interface Stream { [Symbol.asyncIterator](): any; read(): void }
declare const stdin: Stream & { fd: 0 };
interface Typed { [Symbol.asyncIterator](): AsyncIterator<number> }
declare const typed: Typed & { fd: 1 };
export async function f(n: never) {
  for await (const chunk of stdin) {
    const z: number = chunk;
    void z;
  }
  for await (const v of typed) {
    const w: string = v;
    void w;
  }
  for (const x of n) {
    const y: string = x;
    void y;
  }
}
