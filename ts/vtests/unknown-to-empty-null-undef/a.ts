// unknown is assignable to {} | null | undefined (what it stands for); a constraint of it then
// holds an inference of unknown (xstate's setup guards: Record<string, NonReducibleUnknown>)
declare const u: unknown;
const x: {} | null | undefined = u;
const y: Record<string, {} | null | undefined> = { a: u };
declare function g<T extends Record<string, {} | null | undefined> = {}>(o: { [K in keyof T]: (n: number) => void }): T;
const r = g({ a: (n) => {} });
const rr: number = r;
