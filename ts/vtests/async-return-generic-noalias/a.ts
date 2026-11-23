// an async function's returns: awaited without Awaited<T> for generic types (getAwaitedTypeNoAlias),
// T & {} of a narrowed T | undefined against T; awaiting T & {} elsewhere: Awaited<T & {}>
export async function g<T>(x: T & {}, y: Promise<T & {}>): Promise<string> { if (x) return x; return y; }
export async function f<T>(a: T & ({} | null), b: T & {}, x: T | undefined): Promise<T> {
  if (b) return b;
  if (x !== undefined) { const q: number = x; return x; }
  return a;
}
export async function f0<T>(x: T & {}, y: Promise<T & {}>): Promise<T> { if (x) return 1; return y; }
