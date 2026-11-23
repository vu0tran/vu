interface Sheet { key: string; scores: Map<string, number> }
declare const byId: Map<string, Map<string, number>>;
declare const rows: { id: string; key: string }[];
// the receiver is the callback's declared return (U), not U as the annotation infers it
export const sheets: Sheet[] = rows.map((row) => ({
  key: row.key,
  scores: byId.get(row.id) ?? new Map<any, any>(),
}));
export const sheets3 = rows.map((row): Sheet => ({ key: row.key, scores: new Map<any, any>() }));
declare function id<T>(f: () => T): T;
export const s4: Sheet = id(() => ({ key: '', scores: new Map<any, any>() }));
export const s6 = id<Sheet>(() => ({ key: '', scores: new Map<any, any>() }));
declare function id7<T>(f: () => { a: Map<string, number>; b: T }): T;
export const x7 = id7(() => ({ a: new Map<any, any>(), b: 1 }));
export const x8: Sheet = id7(() => ({ a: new Map<any, any>(), b: { key: '', scores: new Map<any, any>() } }));
declare function id9<T>(t: T, f: (n: number) => T): T;
declare const sh: Sheet;
export const x9 = id9(sh, (n) => ({ key: '', scores: new Map<any, any>() }));
export const x10: Sheet = id(function () { return { key: '', scores: new Map<any, any>() }; });
export const one: Sheet = { key: '', scores: byId.get('') ?? new Map() };
declare function id5<T extends Sheet>(f: () => T): T;
export const s5 = id5(() => ({ key: '', scores: new Map<any, any>() }));
