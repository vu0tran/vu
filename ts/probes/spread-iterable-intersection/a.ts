interface Tagged<T> {
  readonly tag: T;
}
interface Listy<T> extends Array<T> {
  clearAll(): T[];
}
export enum Color {
  Red = 'red',
  Blue = 'blue',
}

declare const names: Listy<string> & Tagged<'n'>;
declare const colors: Listy<Color> & Tagged<'c'>;

export function take(xs: string[], cs: Color[]): number {
  return xs.length + cs.length;
}

export const n1 = take([...names], [...colors]);
export const n2: Color[] = [...colors];
export const n3: string[] = [...names, 'x'];
for (const s of names) void s;

export enum Level {
  Low,
  High,
}
declare const nums: Listy<number> & Tagged<'x'>;
export const lv: Level[] = [...nums];
export const lv2: Level[] = [...nums.clearAll()];

export function copy(): void {
  document.execCommand('copy');
}
