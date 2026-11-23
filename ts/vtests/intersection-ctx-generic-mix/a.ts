type Run = (<R>(func: (...args: any[]) => R, ...args: any[]) => Promise<R>) & ((fn: (selector: string) => number, selector: string) => Promise<number>);
declare const doc: { runJsFunction: Run };
doc.runJsFunction = async () => {
  throw new Error('x');
};
const n: number = 'x';
export {};
