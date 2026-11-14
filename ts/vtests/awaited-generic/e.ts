type JE<P extends object> = P & { version: number };
declare function tr<P extends object>(r: string): Promise<JE<P> | null>;
export async function f<P extends object>(refs: string[][]) {
  for (const batch of refs) {
    const results = await Promise.all(batch.map(async (ref) => await tr<P>(ref)));
    results.forEach((entry) => {
      const q: number = entry;
    });
  }
}
export async function g<P extends object>(batch: string[]) {
  const results = await Promise.all(batch.map(async (ref) => await tr<P>(ref)));
  results.forEach((entry) => {
    const q: number = entry;
  });
}
