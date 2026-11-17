export {};
type Out = { status: 'c'; r: number } | { status: 'f'; e: string };
type Sub = { kind: 's' } & Out;
type RC = { kind: 'd' } | Sub;
const c1: RC = { kind: 's', status: 'c', r: 1 };
type RC2 = { kind: 'd' } | ({ kind: 's' } & { status: 'c'; r: number }) | ({ kind: 's' } & { status: 'f'; e: string });
const c2: RC2 = { kind: 's', status: 'c', r: 1 };
