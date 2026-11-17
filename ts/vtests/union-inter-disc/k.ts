export {};
type Out = { status: 'c'; r: number } | { status: 'f'; e: string };
type RC = { kind: 'd' } | { kind: 'q'; o: number } | ({ kind: 's' } & Out);
const c1: RC = { kind: 's', status: 'c', r: 1 };
