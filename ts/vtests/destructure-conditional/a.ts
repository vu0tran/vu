type Opt<T extends object, V> = {} extends V ? [param?: T | undefined] : [param: T];
type O = { skip?: boolean; n: number };
export function q<V extends object = {}>(...[options]: Opt<O, V>) {
  const a: number = options;
  const s = options?.skip;
  const t: string = s;
  return options;
}
const r: string = q();
declare const skip: 'skip';
type Skip = typeof skip;
type Opt2<T, V> = {} extends V ? [param?: T | undefined] : [param: T];
export function w<V extends object = {}>(...[options]: Opt2<O | Skip, V>) {
  const on = options !== skip && options?.n;
  const bad = options === 'x';
  return on;
}
