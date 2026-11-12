export enum Color { Red, Green = 5, Blue }
export enum Dir { Up = "UP", Down = "DOWN" }
export const enum Flags { None = 0, A = 1 << 0, B = 1 << 1, AB = A | B }
enum One { Only = 1 }
export const c1: Color = Color.Red;
export const c2: Color = 5;
export const c3: Color = 7;
export const c4: number = Color.Blue;
export const c5: string = Color.Green;
export const d1: Dir = "UP";
export const d2: string = Dir.Up;
export const d3: Dir.Up = Dir.Down;
export let c6 = Color.Red;
export const c7: "x" = c6;
export const f1: Flags = Flags.AB;
export const f2: 3 = Flags.AB;
export const f3: 4 = Flags.AB;
export function sw(c: Color): string {
  switch (c) {
    case Color.Red: return "r";
    case Color.Green: return "g";
    case Color.Blue: return "b";
  }
}
export function nm(c: Color) { return Color[c]; }
export const o: One = One.Only;
export const o2: string = o;
export type K = keyof typeof Color;
export const k: K = "Pink";
export function eq(c: Color, d: Dir) { if (c === Color.Red) { const x: Color.Red = c; return x; } return d === Dir.Up; }
export const n: number = Color;
