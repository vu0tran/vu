// A property of an any value isn't narrowed (tsc returns any before flow analysis); an element
// access with a literal key is.
declare const rules: any;
declare const key: string;
if (typeof rules.host === 'string') {
  const h: number = rules.host;
  const h2: number = rules?.host;
  console.log(h, h2);
}
if (typeof rules['k'] === 'string') {
  const k: number = rules['k'];
  console.log(k);
}
rules.x = 'a';
const x: number = rules.x;
const s = typeof rules.name === 'string' ? rules.name : key;
const t: number = s;
declare let o: { a: any };
if (typeof o.a.b === 'string') {
  const b: number = o.a.b;
  console.log(b);
}
if (typeof o.a === 'string') {
  const a: number = o.a;
  console.log(a);
}
console.log(x, t);
export {};
