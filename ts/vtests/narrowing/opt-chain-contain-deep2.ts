type P = { type?: string; name?: unknown };
export function f(callee: { property?: P } | undefined, c2: { property: P } | undefined) {
  if (callee?.property?.type === 'Identifier') { callee.property.name; }
  if (c2?.property.type === 'Identifier') { c2.property.name; }
  if (callee?.property?.type) { callee.property.name; }
}
