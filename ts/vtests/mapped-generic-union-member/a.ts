// A generic mapped source to a union: some member (typeRelatedToSomeType). Two copies of one
// class (two @types/react) compare setState's parameter structurally: Pick<{}, K> to
// Pick<{}, K> | {} | (fn) | null, each {} written apart. A concrete source to a generic mapped
// target over K: K related to keyof S, then S[P] to the template (keyof {} is never).
declare namespace RA {
  class Component<P, S> {
    setState<K extends keyof S>(state: ((prevState: Readonly<S>, props: Readonly<P>) => Pick<S, K> | S | null) | (Pick<S, K> | S | null), callback?: () => void): void;
  }
}
declare namespace RB {
  class Component<P, S> {
    setState<K extends keyof S>(state: ((prevState: Readonly<S>, props: Readonly<P>) => Pick<S, K> | S | null) | (Pick<S, K> | S | null), callback?: () => void): void;
  }
}
declare let x: RA.Component<any, {}>;
export const y: RB.Component<any, {}> = x;
declare let x2: RA.Component<any, { a: number }>;
export const y2: RB.Component<any, { a: number }> = x2;

export function g<K extends never>(f: () => void): Pick<{}, K> { return f; }
export function h<K extends "a">(o: { a: number; b: string }): Pick<{ a: number }, K> { return o; }
export function h2<K extends "a">(o: { b: string }): Pick<{ a: number }, K> { return o; }
export function h4<K extends "a" | "b">(o: { a: number }): Pick<{ a: number; b: number }, K> { return o; }

export function u<K extends never>(p: Pick<{}, K>): Pick<{}, K> | string { return p; }
export function u2<K extends "a">(p: Pick<{ a: number }, K>): Pick<{ a: number }, K> | null { return p; }
export function u4<K extends "a">(p: Pick<{ a: number }, K>): { b: string } | null { return p; }
export function u5<K extends "a">(p: Pick<{ a: number }, K>): string | number { return p; }
