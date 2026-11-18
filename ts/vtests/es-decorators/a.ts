function good(value: () => string, ctx: ClassGetterDecoratorContext) { return value; }
function goodn(v: () => number, ctx: ClassMethodDecoratorContext): void {}
function bad3(a: number, b: string) {}
class K {
  @Memoized
  get a() { return 'x'; }
  @Memoized
  private get b() { return [1]; }
  @good
  get c() { return 'y'; }
  @good
  get d() { return 1; }
  @goodn
  m() { return 1; }
  @bad3
  n() {}
  @Memoized
  static get s() { return true; }
}
declare function Service(): Function;
@Service()
export class S1 { }
