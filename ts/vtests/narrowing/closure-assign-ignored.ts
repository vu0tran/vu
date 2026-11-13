export function g() {
  let x: string | number = 'a';
  for (const i of [1]) { const f = () => { x = 1; }; f(); const z: 'z' = x; }
  if (Math.random()) { [1].forEach(() => { x = 2; }); }
  const y: 'z' = x;
}
