declare global {
  namespace globalThis {
    var buildIt: (n: number) => string;
    var SafeObject: typeof Object;
  }
}
export const a: number = globalThis.buildIt(1);
export const b = buildIt(2);
export const k = globalThis.SafeObject.keys({});
