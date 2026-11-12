// this in an object literal's methods: the contextual signature's this, ThisType<T>, else the
// literal's contextual type
export {};
interface Opts { transform?(this: Stream, chunk: any, done: () => void): void; flush?(this: Stream, done: () => void): void; name?: string }
declare class Stream { push(x: any): boolean; }
declare function make(o: Opts): Stream;
make({
  transform(chunk: number, done) { this.push(chunk); done(); },
  flush(done) { this.push(1); const n: number = this; done(); },
});
interface P { a: number; m(): number }
const p: P = { a: 1, m() { const s: string = this.a; return this.a; } };
type T = { x: number } & ThisType<{ y: string }>;
const t: T = { x: 1, ...{}, };
const t2: { x: number; f(): void } & ThisType<{ y: string }> = { x: 1, f() { const n: number = this.y; } };
