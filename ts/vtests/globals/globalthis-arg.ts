// globalThis as an argument: an object
export {};
const p = Reflect.get(globalThis, 'process');
const n: number = p;
const k = Object.keys(globalThis);
const q: number = k;
