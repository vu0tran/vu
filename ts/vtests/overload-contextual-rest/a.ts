interface C2 {
  log(message?: any, ...optionalParams: any[]): void;
  log(...data: any[]): void;
}
export const debugLog: C2['log'] = (...args) => { const z: number = args; };
