export {};
type Out = { status: 'completed'; result: number } | { status: 'failed' | 'cancelled'; error: string };
type Sub = { kind: 'subExecution'; executionId: string } & Out;
type RC = { kind: 'deadline' } | { kind: 'request'; outputs: number } | Sub;
declare function resume(id: string, c: RC): void;
declare const outcome: Out;
resume("a", { kind: 'subExecution', executionId: "x", ...outcome });
const c1: RC = { kind: 'subExecution', executionId: "x", status: 'completed', result: 1 };
const c2: RC = { kind: 'subExecution', executionId: "x", status: 'completed', error: "e" };
