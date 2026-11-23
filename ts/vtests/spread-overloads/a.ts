interface C2 {
  log(message?: any, ...optionalParams: any[]): void;
  log(...data: any[]): void;
}
declare const con: C2;
export const debugLog: C2['log'] = (...args) => { con.log(...args); };
declare function f(a: string, ...r: number[]): number;
declare function f(a: string, ...r: string[]): string;
declare const ns: number[];
declare const ss: string[];
const x: boolean = f('a', ...ns);
const y: boolean = f('a', ...ss);
