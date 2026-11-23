// for await over a type whose [Symbol.asyncIterator] is declared twice (two copies of @types/node
// merging ReadableStream): the element type they agree on
export async function f(b: RS<Uint8Array>) {
  for await (const chunk of b) {
    const n: string = chunk;
  }
}
