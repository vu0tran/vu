// A mapped type with an as clause over keys that are object types: each named by the as clause,
// as TanStack Form's DeepRecord is ({ [R in DeepKeysAndValues<T> as R['key']]: R['value'] }).
type KV = { key: 'email'; value: string } | { key: 'age'; value: number } | { key: `n.${number}`; value: boolean };
type DR<T extends { key: string; value: unknown }> = { [R in T as R['key']]: R['value'] };
export const a1: number = null! as DR<KV>['email'];
export const a2: string = null! as DR<KV>['age'];
export const a3: number = null! as keyof DR<KV>;
declare const d: DR<KV>;
export const a4: number = d.email;
export const a5: number = d['n.3'];
type Drop<T extends { key: string; value: unknown }> = { [R in T as R['value'] extends string ? never : R['key']]: R['value'] };
export const a6: number = null! as keyof Drop<KV>;
