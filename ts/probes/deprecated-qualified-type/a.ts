import * as ns from './lib';
import { lib } from './reexp';
import { Old } from './lib';

export namespace N {
  /** @deprecated inner */
  export type In = string;
  export type Ok = number;
}

export const f = <T extends ns.Old>(s: T) => s;
export const g = <T extends lib.Old>(s: T) => s;
export type H = lib.OldI | ns.Base | N.In | N.Ok;
export type I = Old<number>;
export let j: ns.Old<string> | undefined;
