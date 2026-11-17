export {};
type AF = (...args: any) => any;
function g<T extends AF>(fn: T, ...p: Parameters<T>): ReturnType<T> { return fn(...p); }
interface D<T extends AF> { (...args: Parameters<T>): ReturnType<T> | undefined }
function h<T extends AF>(d: D<T>, ...p: Parameters<T>) { const r: number = d(...p); return r; }
