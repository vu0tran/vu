enum E { A = 1 }
declare const anyv: any;
type Ctx = { vars: { n: string; e: E } };
type Nav = { go: (doc: Ctx, n?: string, e?: E, z?: unknown) => Promise<void> };
export const nav: Nav = { go: async () => {} };
nav.go = async (doc, n = doc.vars.n, e = 1, z = anyv.x) => { void doc; void n; void e; void z; };
nav.go = async (doc, n = undefined) => { void n; };
export class C {
  #value = '';
  #e: E = E.A;
  #a = anyv;
  get value(): string { return this.#value; }
}
