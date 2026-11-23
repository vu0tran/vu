// a spread of a tuple ending in a rest element ([func: F, ...args: any[]], Parameters of a generic
// function) to a generic function: its fixed elements arguments, its rest a spread of its array
interface Ctx { run: <R>(func: (...args: any[]) => R, ...args: any[]) => Promise<R> }
declare const doc: Ctx;
const read = doc.run;
doc.run = async (...args) => {
  const r = read(...args);
  const n: number = r;
  return r;
};
export const f = (async (...args: Parameters<Ctx['run']>) => {
  const q = read(...args);
  const m: number = q;
  return q;
}) as Ctx['run'];
declare function g<T>(a: T, ...rest: string[]): T;
declare const tup: [number, string, string];
export const h: string = g(...tup);
