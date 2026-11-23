declare const x: any;
declare const xs: any[];
export function f(a: bigint): number;
export function f(a: bigint | undefined): number | null;
export function f(a: bigint | undefined): number | null {
  if (a === undefined) return null;
  return x;
}
export function g(a: string): string;
export function g(a: number): any;
export function g(a: string | number): unknown {
  return x;
}
export function h(a: string): string[];
export function h(a: number): number[];
export function h(a: string | number): string[] | number[] {
  return xs;
}
export function k(a: string): Promise<string>;
export async function k(a: string): Promise<string> {
  return x;
}
