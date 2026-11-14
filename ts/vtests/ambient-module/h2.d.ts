declare module 'm2' {
  import { x } from 'other';
  export const y: typeof x;
  export interface I { a: number }
}
declare module 'm2' {
  export interface I { b: string }
  export const z: I;
}
