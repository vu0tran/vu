// calling a union of functions with different parameters: the combined signature
export {};
declare const f: ((x: string) => number) | ((y: number, z?: boolean) => string);
f();
f(1 as never, true, 3);
declare const g: ((a: string, b?: number) => void) | ((a: string) => void);
g("x", 1);
g("x", "y");
