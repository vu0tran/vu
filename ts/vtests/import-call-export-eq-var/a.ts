// import() of a module whose export = is a variable: its type's properties (this as that type) and a default

export async function f() {
  const m = await import('zz');
  const { default: Z } = m;
  const z = new Z();
  const n: string = z.count;
  const k: string = m.count;
  const d: number = m;
}
