import type { DS } from 'nope-missing';
declare const ds: DS;
declare const ids: { id: string }[];
async function f() {
  const repo = ds.getRepository(1);
  const rows = await Promise.all(ids.map(async ({ id }) => await repo.find(id)));
  rows.map((r) => r);
  const p = ids.map(async ({ id }) => await repo.find(id));
  const q: null = p;
  const rows2 = await Promise.all(p);
  const z: null = rows2;
  const p3 = ids.map(async ({ id }) => repo.find(id));
  const q3: null = p3;
  const w = await repo.find(1);
  const q4: null = w;
}
