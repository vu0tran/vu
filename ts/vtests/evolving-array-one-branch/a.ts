// let x = [] assigned an array in one branch only: the unevolved side is the implicit any[], which the
// join keeps (TS7034 and TS7005, as tsc), fetchResourceWithOverridesByAddress.ts
declare function fo(): Promise<{ id: string }[]>;
export async function sv(c: boolean) {
  let lo = [];
  if (c) {
    lo = await fo();
  }
  const z: number = lo;
}
