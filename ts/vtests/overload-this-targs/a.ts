// overloads declaring this, called with type arguments: each candidate instantiated by them, then
// one whose this doesn't fit isn't applicable
interface Base { base: true }
interface Ctx extends Base { user: string }
declare class Server<in out C extends Base = Base> {
  ctx: C;
  run<T = string, V extends object = {}>(this: Server<Base>, req: { v?: V }): Promise<T>;
  run<T = string, V extends object = {}>(req: { v?: V }, opts?: { ctx: C }): Promise<T[]>;
  pick<T>(this: Server<Base>, x: T): T;
  pick<T>(this: Server<Ctx>, x: T, y: number): T[];
}
declare const s1: Server;
declare const s2: Server<Ctx>;
const a1: number = s1.run<boolean, { a: 1 }>({ v: { a: 1 } });
const a2: number = s2.run<boolean>({}, { ctx: { base: true, user: 'u' } });
const a3: number = s2.run<boolean>({});
const a4: number = s1.pick<string>('x');
const a5: number = s2.pick<string>('x', 1);
const a7 = s1.run<boolean, string>({});
export { a1, a2, a3, a4, a5, a7 };
