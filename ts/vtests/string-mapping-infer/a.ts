declare function toLower<T extends string = string>(value?: T): Lowercase<T>;
declare function startCase(str?: string): string;
declare function up<T extends string>(v: Uppercase<T>): T;
export function f(value: string | null): string {
  if (!value) return '-';
  return startCase(toLower(value));
}
const a: number = toLower('AbC');
declare const u: Uppercase<'x' | 'y'>;
const b: number = up(u);
const c2: number = up('AB');
