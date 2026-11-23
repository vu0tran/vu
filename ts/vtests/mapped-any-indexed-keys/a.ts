type NP<T> = {
  [P in keyof T]-?: undefined extends T[P] ? P : null extends T[P] ? P : never
}[keyof T];
type K<T> = { [P in keyof T]-?: P }[keyof T];
type C1<T> = { [P in keyof T]-?: undefined extends T[P] ? P : never }[keyof T];
type C2<T> = { [P in keyof T]-?: undefined extends T[P] ? P : never };
export const a: number = null as unknown as NP<any>;
export const b: number = null as unknown as K<any>;
export const c: number = null as unknown as C1<any>;
export const d: number = null as unknown as C2<any>[string];
