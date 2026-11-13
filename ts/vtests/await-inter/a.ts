type JE<P extends object> = P & { version: number };
function f<P extends object>(e: JE<P>, g: P & { a?: string }) {
  const v: string = e.version;
  const a: number = g.a;
  e.missing;
}
async function h<P extends object>(p: Promise<JE<P>>) { const r = await p; const s: string = r.version; }
export {};
async function h2<P>(p: P & { a: 1 }) { const r = await p; const s: string = r; }
