import * as Transport from 'tr';
interface CI extends Transport { eol: string; }
interface CO extends Transport.TransportStreamOptions { x?: number; }
declare const c: CI;
const n: number = c.level;
const o: CO = { level: "a", x: 1, silent: 3 };
const e: string = c.eol;
