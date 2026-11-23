// object literal methods and accessors with a computed name the binder names (a well-known symbol,
// a literal, a unique symbol constant): properties of that name
declare const tag: unique symbol;
const o = {
  append(d: string) { return d.length; },
  async [Symbol.asyncDispose]() { return; },
  ['lit'](x: number) { return x; },
  [tag]() { return 1; },
  get ['g']() { return 's'; },
};
export const a: string = o.lit(1);
export const b: number = o[Symbol.asyncDispose];
export const c: string = o[tag]();
export const d: number = o.g;
await using r = o;
export { r };
