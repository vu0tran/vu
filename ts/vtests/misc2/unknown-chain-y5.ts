declare const p: { [k: string]: unknown };
declare const k: string;
p[k].toString();
(p.x as unknown).toString();
p.x.toString();
export {};
