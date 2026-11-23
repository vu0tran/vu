// (a parameter whose type has undefined, with an initializer whose type doesn't: read without
// undefined in its body and in functions in it, until it's assigned; removeOptionalityFromDeclaredType)
declare function g(o?: { s?: string }): number;
type P0 = Parameters<typeof g>[0];
const f1 = (o: { s?: string } | undefined = {}) => o.s;
const f2 = (o: P0 = {}) => o.s;
function f3(o: Parameters<typeof g>[0] = {}) { return o.s; }
const f5 = (o: { s?: string } | undefined = {}): string | undefined => o.s;
function f7(o: { s?: string } | undefined = {}) { return () => o.s; }
function f8(o: { s?: string } | undefined = {}) { o = undefined; return () => o.s; }
function f9(o: { s?: string } | undefined = {}) { o = undefined; return o.s; }
// (an initializer that may be undefined: undefined stays)
declare const maybe: { s?: string } | undefined;
const f10 = (o: { s?: string } | undefined = maybe) => o.s;
export {};
