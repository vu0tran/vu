type R = { workflowId: string };
type D = ({ id: string } & R & { awaited: true }) | ({ id: string } & R & { awaited: false });
type Want = { id: string; awaited: true; workflowId: string };
declare const ctx: { d: D | undefined };
function f(): Want | undefined {
  const { d } = ctx;
  if (d?.awaited) return d;
  return undefined;
}
function g(d: D | undefined): Want | undefined {
  if (d?.awaited) return d;
  return undefined;
}
function h(d: D): Want | undefined {
  if (d.awaited) return d;
  return undefined;
}
type E = { k: true; a: 1 } | { k: false; b: 2 };
function i(e: E | undefined): { k: true; a: 1 } | undefined {
  if (e?.k) return e;
  return undefined;
}
export {};
function j(e: E | undefined): { k: false; b: 2 } | undefined {
  if (!e?.k) return e;
  return undefined;
}
function j2(e: E | undefined) {
  if (!e?.k) { const z: { k: false; b: 2 } = e; }
  else { const z: { k: true; a: 1 } = e; }
  if (e?.k === true) { const z: { k: true; a: 1 } = e; }
}
