declare const xs: { address?: { uuid?: string }; token?: string; readonly ro?: { v?: string } }[];
xs.map((e) => {
  const has = !!e.address?.uuid && !!e.token;
  if (has) {
    const u: string = e.address!.uuid!;
    const t: number = e.token.length;
  }
  const r = !!e.ro;
  if (r) { const v: number = e.ro; }
  const k = e !== undefined;
  if (k) { const w: number = e; }
});
export {};
