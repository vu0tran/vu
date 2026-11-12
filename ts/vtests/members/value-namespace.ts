export namespace V {
  export const x = 1;
  export let y = "s";
  const hidden = true;
  export function f(n: number): number { return n + x; }
  export function g(): boolean { return hidden; }
  export namespace In { export const z: number = f(2); }
}
export const a: string = V.x;
export const b: number = V.y;
export const c2: string = V.In.z;
export const d = V.hidden;
V.y = "t";
V.x = 2;
export const e: string = V.f(1);
