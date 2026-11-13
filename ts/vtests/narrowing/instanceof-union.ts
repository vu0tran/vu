// instanceof on a union nothing in which is derived: the union's intersection with the class
export {};
interface P { [key: string]: V }
interface RL { __rl: true; mode: string }
type V = string | number | boolean | null | undefined | P | RL | { type: "icon"; value: string } | P[] | RL[] | string[];
declare const v: V;
if (v instanceof Date) { const n: number = v; } else { const n: number = v; }
declare const w: string | P[] | RL;
if (w instanceof Date) { const n: number = w; } else { const n: number = w; }
declare const x: P;
if (x instanceof Date) { const n: number = x; }
