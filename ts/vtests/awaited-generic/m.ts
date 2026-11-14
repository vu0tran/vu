type JE<P extends object> = P & { version: number };
declare function tr<P extends object>(r: string): Promise<JE<P> | null>;
export async function g<P extends object>(refs: string[][]) {
  const entries = new Map<string, JE<P>>();
  for (const batch of refs) {
    const results = await Promise.all(batch.map(async (ref) => await tr<P>(ref)));
    results.forEach((entry, idx) => {
      if (entry) entries.set(batch[idx], entry);
    });
  }
}
