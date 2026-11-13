// typeof x === 'object' / 'function' on a type parameter: T & object (and T & null), T & Function
export function d1<T extends object | string>(source: T): T {
  if (typeof source !== 'object') { const a: number = source; return source; }
  const b: number = source;
  return source;
}
export function d2<T>(v: T) { if (typeof v === 'object') { const a: number = v; } else { const b: number = v; } }
export function d3<T>(v: T) { if (typeof v === 'function') { const a: number = v; } }
export function d4<T>(v: T) { if (typeof v === 'number') { const a: string = v; } else { const b: number = v; } }
