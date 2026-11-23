// no-unnecessary-type-assertion on a generic call through an intersection of signatures (testing-library screen.getByRole(...) as HTMLButtonElement)
interface El { tag: string }
interface Btn extends El { press(): void }
declare const f: (<T extends El = El>(id: string) => T) & ((id: string) => El);
export const n1 = f("x") as Btn;
type S = { get<T extends El = El>(id: string): T } & { get: (id: string) => El };
declare const s: S;
export const n2 = s.get("x") as Btn;
declare const g: <T extends El = El>(id: string) => T;
export const n3 = g("x") as Btn;
