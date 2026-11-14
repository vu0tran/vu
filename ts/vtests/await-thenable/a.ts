interface PWC<T> extends Promise<T> { child: number }
declare const p1: PWC<{ stdout: string }>;
declare const t1: { then(f: (v: number) => void): void };
declare const t2: { then(f?: ((v: string) => void) | null, r?: (e: any) => void): void };
declare const t3: { then(f: (v: PromiseLike<boolean>) => void): void };
async function f() {
  const { stdout } = await p1;
  const a: number = stdout;
  const b: string = await t1;
  const c: number = await t2;
  const d: string = await t3;
}
export {};
