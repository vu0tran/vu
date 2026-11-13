export function f(value: any, v2: any) {
  if (typeof value === 'object' && Object.keys(value).length === 0) { }
  const b = v2 && typeof v2 === 'object' && !Array.isArray(v2) && !!Object.keys(v2).length;
  if (typeof value === 'object') { const z: 'z' = value; }
  return b;
}
