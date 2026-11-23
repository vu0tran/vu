// Two variables whose initializers read each other (drizzle's tables and their foreign keys):
// a's type asks for b's, whose initializer has a function with a written return type; its body
// waits until a has its type too, so it reads a as tsc does.
declare function table<T>(name: string, cols: T, extra?: (t: T) => unknown[]): { [K in keyof T]: T[K] };
declare function ref(f: () => number): number;
export const a = table('a', { id: 1 }, (t) => [t.id, b.x]);
export const b = table('b', { x: ref((): number => { const q: string = a; return a.id; }) });
const s: string = a.id;
