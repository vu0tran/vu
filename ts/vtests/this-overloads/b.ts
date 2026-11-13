interface Ctx { a: number }
declare const f: (this: Ctx) => Promise<number>;
async function m() {
  const r = await f.call({ a: 1 });
  const s: string = r;
}
function m3() { const q = f.call({ a: 1 }); const z: string = q; }
export {};
