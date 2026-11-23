interface Con {
  log(message?: any, ...rest: any[]): void;
  log(...data: any[]): void;
  warn(message?: string, ...rest: number[]): number;
}
declare const con: Con;
declare function one(a: string, b?: number, ...r: number[]): string;
function f(...args: unknown[]) {
  const a: string = con.log(...args);
  const ns: number[] = [];
  const c: number = one("x", ...ns);
  const d: number = one(...ns);
  const e: string = one("x", ...["a"]);
  const strs: string[] = [];
  const g: string = one("x", ...strs);
}
