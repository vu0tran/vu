declare function mk(): Promise<{ url: string; stop: () => Promise<void>; n?: number }>;
let url: string;
let stop: () => Promise<void>;
let n: number | undefined;
const o: { u: string } = { u: '' };
async function f() {
  ({ url, stop } = await mk());
  const a: null = url;
  ({ url: o.u, n } = await mk());
  const b: null = n;
  ({ n: url } = await mk());
  ({ zz: url } = await mk());
}
const k = 1;
declare const src: { k: number; m: any };
({ k } = src);
let q: string;
({ m: q } = src);
const c: null = q;
({ k: q } = { k: 'x' });
export {};
