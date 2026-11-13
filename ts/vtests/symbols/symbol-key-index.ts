declare const SYM: unique symbol;
interface D { [key: string]: string | boolean | undefined; [SYM]?: { a: 1 }; name: string }
declare function mk<K extends string>(f: Record<K, number>): Record<K, string> & { [SYM]: { a: 1 } };
export const d: D = { name: 'x', ...mk({ path: 1 }) };
export const d2: D = { name: 'x', [SYM]: { a: 1 } };
export const d3: D = { name: 'x', [SYM]: { a: 2 } };
