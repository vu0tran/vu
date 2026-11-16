enum K { Spread = 'SpreadElement', Id = 'Identifier' }
interface Spread { type: K.Spread; argument: number }
interface Ident { type: K.Id; name: string }
type Arg = Spread | Ident;
export function f(args: Arg[]): number {
  for (const arg of args) {
    if (arg.type !== 'SpreadElement') continue;
    return arg.argument;
  }
  return 0;
}
export function g(a: Arg): string {
  if (a.type === 'Identifier') return a.name;
  return String(a.argument);
}
export function h(a: Arg): string {
  switch (a.type) {
    case 'Identifier': return a.name;
    case 'SpreadElement': return String(a.argument);
  }
}
export function i(a: Arg): string {
  switch (a.type) {
    case K.Id: return a.name;
    default: return String(a.argument);
  }
}
export function j(t: K): number { if (t === 'Identifier') { const x: K.Id = t; void x; } return 1; }
