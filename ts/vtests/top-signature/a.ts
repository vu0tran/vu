// a top signature, (...args: any) => any: every function type relates to it (isTopSignature), as
// ReturnType's constraint takes a function of a never parameter
export {};
declare const v: never;
function conv(values: typeof v) { return { a: 1 as const, b: values }; }
type R = ReturnType<typeof conv>;
const n1: number = null as unknown as R;
type Top = (...args: any) => any;
const f1: Top = (x: never, y: string) => 1;
const f2: (...args: never) => unknown = (x: number) => 'x';
const f3: (...args: any[]) => any = (x: { a: number }) => x;
const f4: (...args: unknown[]) => any = (x: { a: number }) => x;
