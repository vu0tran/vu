// A tagged template whose tag is an intersection of function types: its members' signatures, in
// order, the ones that take as many arguments as the template gives (hasCorrectArity); awaiting an
// intersection with one thenable member: that member's promised type (execa`...`, a
// ChildProcess-like object & Promise<Result>).
type Opt = { shell?: boolean };
type Sub = { pid: number; kill(): void };
type Bind = <N extends Opt = {}>(options: N) => Method;
type Tmpl = (...t: readonly [TemplateStringsArray, ...readonly (string | string[])[]]) => Sub & Promise<{ out: string }>;
type Long = (file: string, args?: readonly string[], options?: Opt) => Sub & Promise<{ out: string }>;
type Method = Bind & Tmpl & Long;
declare const run: Method;
declare const args: string[];
export async function f() {
  const p = run`ls ${args}`;
  const n1: number = p;
  const r = await p;
  const n2: number = r;
  const n3: number = (await run`ls`).out;
  const n4: number = run({ shell: true });
  const n5: number = await run('ls', []);
}
