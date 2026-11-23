// an intersection's signatures from different symbols keep their order (reorderCandidates): the
// generic method first, its T inferred from the return context
type S = { get<T extends HTMLElement = HTMLElement>(role: string): T } & { get: (role: string) => HTMLElement };
declare const s: S;
export const x1: HTMLButtonElement = s.get('b');
type G<T extends HTMLElement = HTMLElement> = (role: string) => T;
type S2 = { get<T extends HTMLElement = HTMLElement>(role: string): T } & { [P in 'get']: G };
declare const s2: S2;
export const x2: HTMLButtonElement = s2.get('b');
type S3 = { get: (role: string) => HTMLElement } & { get<T extends HTMLElement = HTMLElement>(role: string): T };
declare const s3: S3;
export const x3: HTMLButtonElement = s3.get('b');
interface M { f(a: string): string }
interface M { f(a: number): number }
declare const m: M;
export const y1: boolean = m.f(1);
type O = { h(a: 'x'): 1; h(a: string): 2 } & { h(a: string): 3 };
declare const o: O;
export const z1: boolean = o.h('x');
export const z2: boolean = o.h('y');
interface DC { new (v: number): { a: 1 } }
interface DC { new (v: string): { b: 2 } }
declare const DCv: DC;
declare const anyv: any;
export const w1: boolean = new DCv(anyv);
