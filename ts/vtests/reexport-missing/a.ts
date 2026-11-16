// export { x } from a package that isn't there: x is still exported (an error type, any).
import type { Hints, More } from "pk";
import { val } from "pk";
export const h: Hints = 1;
export const m: More = 2;
export const v: number = val;
