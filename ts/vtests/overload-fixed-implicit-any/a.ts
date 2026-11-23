declare function g2(x: { a?: number }): void;
declare function g2(x: ((e: any) => void) & { a?: number }): void;
g2((e) => {});
declare function g3(x: number): void;
declare function g3(x: ((e: any) => void) & { a?: number }): void;
g3((e) => {});
declare function g7(x: { a?: number }): void;
declare function g7(x: ((e: string) => void) & { a?: number }): void;
g7((e) => { const n: number = e; });
