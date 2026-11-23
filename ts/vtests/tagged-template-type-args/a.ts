// tag<T>`...`: the tag's signature instantiated with the type arguments, as a call's (drizzle's sql<number>`...`).
interface SQL<T = unknown> { _t: T; mapWith<U>(f: (x: unknown) => U): SQL<U> }
declare function sql<T = unknown>(strings: TemplateStringsArray, ...params: unknown[]): SQL<T>;
declare function sqlc<T extends string>(strings: TemplateStringsArray, ...params: unknown[]): SQL<T>;
const a = sql<number>`select ${1}`;
const b: string = a;
const c: SQL<string> = sql<number>`x`;
const d = sql`y`;
const e: number = d;
const f: number = sqlc<"a">`z`;
