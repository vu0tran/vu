declare function f(): Promise<number>;
const x = await f();
const y: null = x;
const z = await 5;
for await (const q of [Promise.resolve('a')]) { const w: null = q; }
export {};
