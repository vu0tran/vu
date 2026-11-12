// Awaiting a type parameter: Awaited<T> (itself for a non-thenable constraint)
export {};
async function w<T>(fn: () => Promise<T>): Promise<T> { return await fn(); }
async function w2<T>(fn: () => Promise<T>): Promise<T> { const r = await fn(); return r; }
async function w3<T>(fn: () => Promise<T>): Promise<number> { const r = await fn(); return r; }
async function w4<T extends string>(fn: () => Promise<T>): Promise<T> { const r = await fn(); const n: number = r; return r; }
async function w5<T>(p: Promise<T>) { const r = await p; const n: number = r; }
