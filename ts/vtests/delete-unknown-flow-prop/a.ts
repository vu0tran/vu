// delete x.a reads x.a, whose flow type doesn't matter there (a property assigned in a loop).
declare const env: { [k: string]: string | undefined };
declare function f(): boolean;
export function t1() {
  env.A = 'x';
  for (const p of ['', 'y']) {
    env.A = p;
    f();
  }
  delete env.A;
  env.A = 'z';
  const n: number = env.A;
}
