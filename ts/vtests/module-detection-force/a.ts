// moduleDetection force: aug.ts has no import or export but is a module, so its declare module
// 'lib1' augments the package instead of replacing it
import { z, type Register } from 'lib1';
const n: number = z.s();
declare const r: Register;
const m: string = r.a;
