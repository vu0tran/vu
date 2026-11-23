// awaiting an intersection: members without a then contribute nothing; several with one, their
// promised types united (getPromisedTypeOfPromise over the intersection's then signatures)
type Brand = string & { __b: 1 };
declare const b: Brand;
declare const pp: Promise<number> & Promise<string>;
declare const xp: { kill(): void } & Promise<boolean>;
declare const fp: (() => void) & Promise<number>;
export async function f() {
  const r1 = await b;
  const n1: number = r1;
  const r2 = await pp;
  const n2: boolean = r2;
  const r3 = await xp;
  const n3: number = r3;
  const r4 = await fp;
  const n4: string = r4;
}
