// a qualified type name whose left name is only a value (a variable): TS2503, the error type
declare global {
  var optimizely: optimizely.Optimizely;
}
declare const x: number;
type T = x.Y;
export const a: string = null! as T;
export const b: number = globalThis.optimizely;
