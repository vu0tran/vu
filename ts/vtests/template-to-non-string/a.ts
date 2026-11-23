// A generic template literal type is a string: never related to undefined, null, number or the like, nor to a union of them.
function f<T, K extends `${keyof T & string}`>(k: K, t: `a${keyof T & string}`) {
  const a: string | undefined = k;
  const c: undefined = t;
  const d: boolean | string = t;
  const e: null = t;
}
