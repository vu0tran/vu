type JE<P extends object> = P & { version: number };
function f1<T extends object>(a: Awaited<T>): T { return a; }
function f2<T>(a: Awaited<T>): T { return a; }
function f3<P extends object>(a: Awaited<JE<P>>): JE<P> { return a; }
function f4<P extends object>(a: Awaited<JE<P>>): P { return a; }
function f5<P extends object>(a: Awaited<JE<P>>): { version: number } { return a; }
function f6<P extends object>(a: Awaited<JE<P>>): string { return a; }
