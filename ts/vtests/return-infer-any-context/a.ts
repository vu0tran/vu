declare function cb<T = string>(f: (x: T) => void): T;
export const r: any = cb((x) => { const n: number = x; });
declare function take(a: any): void;
take(cb((x) => { const n: number = x; }));
export const s: unknown = cb((x) => { const n: number = x; });
