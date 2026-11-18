declare function f<T>(a: T, b: NoInfer<T>): T;
export const r1: string = f(1, 2);
export const r2 = f('a', 'b');
export const r3: number = r2;
f(1, 'x');
declare function g<O extends unknown[]>(p: (...o: O) => void, ...o: NoInfer<O>): O;
export const r4 = g((a: number, b: string) => {}, 1, 'x');
g((a: number) => {}, 'z');
g((a: number, b: { x: number }) => {}, 1, { x: 'q' });
interface App { use<O>(p: (o: O) => void, o: NoInfer<O>): this; }
declare const app: App;
app.use((o: { a: number }) => {}, { a: 'x' });
export const r5: number = r4;
