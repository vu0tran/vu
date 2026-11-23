declare function create(): Promise<{ run: { id: string; n: 1 }; ids: string[]; k: "a" | "b" }>;
declare function pick<T>(x: T): { run: T; ids: string[] };
async function f() {
  let run;
  let ids: string[];
  let k;
  try {
    ({ run, ids, k } = await create());
  } finally {
  }
  const a: number = run;
  const b: number = ids;
  const d: number = k;
  let r2;
  ({ run: r2 } = pick(1));
  const e: string = r2;
  let r3;
  ({ r3 } = { r3: "lit" as const });
  const g: number = r3;
}
