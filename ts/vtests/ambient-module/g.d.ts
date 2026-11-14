declare module 'riot' {
  interface Brackets { set(token: string): void; }
  type RV = string | null;
  type Fn = (v: string) => RV;
  interface Tmpl extends Fn { eh?(e: Error): void; }
  let brackets: Brackets;
  let tmpl: Tmpl;
  const bad: Missing;
  export function json(s: unknown): unknown;
}
declare module 'other' {
  export const x: number;
}
interface BigInt { toJSON(): string; }
