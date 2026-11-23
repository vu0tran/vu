// a context-sensitive callback in an options literal fixes only what its own contextual
// parameters mention, not what other properties' callbacks would (tanstack queryOptions' select)
type Ctx<K> = { key: K; signal: AbortSignal };
interface Opts<T, K> { select?: (d: T) => T; key: K; fn?: (c: Ctx<K>) => T | Promise<T> }
declare function q<T = unknown, K extends readonly unknown[] = readonly unknown[]>(o: Opts<T, K>): T;
declare function q2<T = unknown, K extends readonly unknown[] = readonly unknown[]>(o: { select?: (d: T) => T, key: K } & { fn?: (c: Ctx<K>) => T | Promise<T> }): T;
declare function f(): Promise<string>;
const a = q({ fn: ({ signal }) => f(), key: ['x'] as const });
const b = q2({ fn: ({ signal }) => f(), key: ['x'] as const });
export const z: [1, 2] = [a, b];
