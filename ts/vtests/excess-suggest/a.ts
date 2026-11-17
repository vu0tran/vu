declare function mk(shape: {a: number}, opts?: { strict?: boolean }): void;
mk({ a: 1 }, { strictt: true });
declare const Base: { new (): { a: number } };
class Over extends Base {
  a: string = "x";
}
const used = new Late();
class Late extends Base {}
