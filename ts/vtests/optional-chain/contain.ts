export {};
declare const r: { o: string; after?: number } | undefined;
declare const x: string;
declare const y: string | undefined;
const a = x === r?.o ? r.after : undefined;
const b = r?.o === x ? r.after : 0;
const c = y === r?.o ? r.after : 0;
const d = r?.o !== x ? 1 : r.after;
