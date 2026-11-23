// a union of template literal keys on a type with a string index signature: each key's property or
// the index signature (a package's previousCursors[`${status}:${dir}:${after}`])
type Status = 'OPEN' | 'DONE';
declare const st: Status;
declare const sortDirection: 'ASC' | 'DESC';
declare const after: string | null;
declare const previousCursors: Record<string, string | null>;
const p = after ? previousCursors[`${st}:${sortDirection}:${after}`] : undefined;
const n: number = p;
declare const m: Partial<Record<string, number>>;
const q: string = m[`${st}:x`];
