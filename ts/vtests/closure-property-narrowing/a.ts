// A property of a constant narrowed outside a function isn't narrowed inside it (tsc goes on to the
// containing function's flow for identifiers only); the constant itself is, and an IIFE's flow is
// the outer one.
declare const ref: { current: HTMLDivElement | null };
declare const u: { kind: 'a'; a: number } | { kind: 'b'; b: string };
declare function later(f: () => void): void;
export function f() {
  if (ref.current) {
    later(() => { const a: number = ref.current; });
    later(function () { const b: number = ref.current; });
    Promise.resolve(1).then(() => { later(function () { const c: number = ref.current; }); });
    (() => { const d: number = ref.current; })();
    const e: number = ref.current;
  }
  if (u.kind === 'a') {
    later(() => { const g: string = u.a; });
    later(() => { const h: string = u.kind; });
  }
}
