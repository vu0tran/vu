// a context-sensitive options literal against a union of option types: its other properties
// still infer in the first pass (t3 env-core's createEnv)
type S = { a: string; b: number };
declare const s: S;
interface Base { onErr?: (issues: readonly string[]) => never }
interface Strict { strict: true }
interface SO<T> { server: Partial<{ [K in keyof T]: T[K] }> }
interface Fin<T> { final?: (shape: T) => unknown }
declare function create<T = {}>(o: ((Base & SO<T>) | (Strict & SO<T>)) & Fin<T>): T;
export const r: boolean = create({ onErr: (i) => { throw new Error(i.join()); }, server: s });
