import isEqual from "lodashlike/isEqual";
import _ from "lodashlike";
import { castArray } from "lodashlike";
export const a: string = isEqual(1, 2);
export const b: string = _.identity(3);
export const c: number[] = castArray("x");
export const d: boolean = _.isEqualWith(1, 2, () => undefined);
