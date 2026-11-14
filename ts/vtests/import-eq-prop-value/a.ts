import { Request } from "sa";
declare class Test extends Request { app: string; }
const t = new Test("x");
const n: number = t.method;
const r: Request = t;
const e: number = r.extra;
