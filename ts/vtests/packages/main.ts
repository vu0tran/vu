import { cond } from "cond";
import { extra } from "cond/extra";
import { plain } from "plain";
import { tv } from "tv";
import { make } from "@sc/pkg";
import { feature } from "sub/feature";

export const a: number = cond(1);
export const b: string = extra.n;
export const c: number = plain().m;
export const d: string = tv;
export const e: string = make().id;
export const f: "g" = feature;
export const ok = cond(2).length + extra.n + plain().m.length + make().id;
