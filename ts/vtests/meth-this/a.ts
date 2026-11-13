interface Opts<T> { read?: ((this: T, size: number) => void) | undefined; go?(this: T): void; }
declare class R { push(x: unknown): boolean; constructor(o?: Opts<R>); }
new R({ read() { this.push(null); const n: number = this; } });
new R({ read(size) { const n: string = this; } });
new R({ go() { const n: string = this; } });
new R({ go(this: R) { const n: string = this; } });
const o: Opts<R> = { read() { this.push(1); } };
export {};
