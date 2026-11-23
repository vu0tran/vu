// class properties with no type and no initializer: their types from the constructor's
// assignments (TypeScript 4.0, noImplicitAny), no TS7008 (a package's AgentRun)
export {};
type Rec = { id: number; chatId: string | null; meta: { n: number } };
class Run {
  readonly id;
  readonly chatId;
  readonly n;
  x;
  y;
  constructor(r: Rec, f: boolean) {
    this.id = r.id;
    this.chatId = r.chatId;
    this.n = r.meta.n;
    if (f) this.x = 1;
    else this.x = 'a';
    if (f) this.y = true;
  }
}
declare const r: Run;
const a: string = r.id;
r.chatId.length;
const b: string = r.n;
r.x = true;
r.y = 1;
