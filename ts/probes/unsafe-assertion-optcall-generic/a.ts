// An asserted call in an optional chain whose signature's type parameter is only in its return
// type: with no-unnecessary-type-assertion on too, tsgolint reads it as any (from `any`).
declare function g<E = number>(s: string): E | null;
declare function h<E extends string = "a">(s: E): E;
declare function k(s: string): number | null;
declare function w<E = number>(s: string): { e: E };
declare const o: { g: typeof g; h: typeof h; k: typeof k; w: typeof w; p: { g: typeof g } } | undefined;
declare const q: { g: typeof g };
declare const card: HTMLElement | null;

export const a1 = o?.g("x") as string | null;
export const a2 = o?.p.g("x") as string | null;
export const a4 = card?.querySelector("span[x]") as HTMLElement;
export const b1 = q.g("x") as 1 | null;
export const b2 = o?.h("x") as "x";
export const b3 = o?.k("x") as 1 | null;
export const b4 = o?.w("x").e as 1;
export function f(label: string) {
  const input = document.querySelector("x");
  const root = (input as HTMLElement | null)?.closest(".M");
  const part = () => root?.querySelector("a" + label) as HTMLInputElement | null;
  return part;
}
declare const root: Element | null;
export const c1 = (root?.querySelector("input[x]") as HTMLInputElement | null)?.value;
export const c2 = (root?.querySelector("input[x]") as HTMLInputElement).value;
export const c3 = (root?.querySelector("input[x]") as HTMLInputElement | null);
export const c4 = (o?.g("x") as { value: string } | null)?.value || "";
declare const d: { getData<V = unknown>(f: string, dflt?: V): V | undefined } | undefined;
export const e1 = d?.getData("x") as string | null;
export const e2 = d?.getData("x", "y") as string | null;
declare const s2: string;
export const f1 = (d?.getData("x") as string) || '';
export const f2 = s2 || (d?.getData("x") as string);
export const f3 = (d?.getData("x") as string) + '';
export const f4 = [d?.getData("x") as string];
export function f5() { return d?.getData("x") as string; }
