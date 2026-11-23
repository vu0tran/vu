// a generic tag: inferred from the substitutions and the call's contextual type
declare class SQL<T = unknown> { _t: T; }
declare function sql<T>(strings: TemplateStringsArray, ...params: any[]): SQL<T>;
declare function exec<R>(q: SQL<R>): R;
declare function pick<T>(s: TemplateStringsArray, a: T, b: T): T[];
const id = 1;
const q = sql`select ${id}`;
const n1: number = q;
const q2: SQL<string> = sql`select 1`;
const n2: number = exec(sql`select ${id}`);
const p = pick`${1} and ${'x'}`;
const n3: number = p;
const p2 = pick`${1} and ${2}`;
const n4: string = p2;
