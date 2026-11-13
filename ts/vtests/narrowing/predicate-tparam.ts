// A type predicate on a type parameter: T & the candidate where it fits T's constraint, T when false
export function f<T extends object | string>(source: T): T {
  if (Array.isArray(source)) {
    const n: number = source;
    const x: number = source.length;
    return source;
  }
  const m: number = source;
  return source;
}
export function g<T>(v: T) {
  if (typeof v === 'string') { const n: number = v; }
  if (Array.isArray(v)) { const n: number = v; } else { const k: number = v; }
}
