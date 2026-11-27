type Msg<N extends string = string> = { readonly $typeName: N; $unknown?: unknown[] };
type Remap<T> = { [P in keyof T as P extends '$unknown' ? never : P]?: T[P] };
type Plain<T> = { [P in keyof T]?: T[P] };
type Item = Msg<'x'> & {
  /** @deprecated old */
  key: string;
  other: string;
};
interface Item2 {
  /** @deprecated old2 */
  key: string;
  other: string;
}

export const a1: Remap<Item> = { key: '' };
export const a2: Plain<Item> = { key: '' };
export const a3: Item | Remap<Item> = { key: '' };
export const a4: Remap<Item2> = { key: '' };
export const a5: Item2 | Plain<Item2> = { key: '' };
type Renamed<T> = { [P in keyof T as P extends string ? `${P}` : never]?: T[P] };
type Kept<T> = { [P in keyof T as P & string]?: T[P] };
type Swap<T> = { [P in keyof T as P extends 'other' ? never : 'key']?: T[P] };
export const a6: Renamed<Item2> = { key: '' };
export const a7: Kept<Item2> = { key: '' };
export const a8: Swap<Item2> = { key: '' };
