const xs: string[] = [];
declare const s: Set<string>;
declare const m: Map<string, number>;
xs.push(...s);
xs.push(...m.keys());
xs.push(...m.values());
declare function f(...a: number[]): void;
f(...s);
f(...m.values());
