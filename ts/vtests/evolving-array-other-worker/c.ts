import { build } from "./a";
const o = build([1]);
export const vs = o.out.map((p) => p.v + 1);
export const z: string = vs;
