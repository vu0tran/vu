interface El { tag: string }
interface Btn extends El { press(): void }
declare const f: (<T extends El = El>(id: string) => T) & ((id: string) => El);
export const n1: Btn = f("x");
type S = { get<T extends El = El>(id: string): T } & { get: (id: string) => El };
declare const s: S;
export const n2: Btn = s.get("x");
declare const g: ((id: string) => El) & (<T extends El = El>(id: string) => T);
export const n3: Btn = g("x");
interface M { h(id: string): El }
interface M { h<T extends El = El>(id: string): T }
declare const m: M;
export const n4: Btn = m.h("x");
interface M2 { h<T extends El = El>(id: string): T }
interface M2 { h(id: string): El }
declare const m2: M2;
export const n5: Btn = m2.h("x");
