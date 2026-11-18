async function f() {
  const m = await import('nope-missing');
  const z: null = m;
  m.x.y;
  const { a } = await import('nope2');
  const q: null = a;
}
export {};
