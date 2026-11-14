declare function D1(t: string, k: string): void;
declare function D2(t: object, k: "a" | "b"): void;
declare function D3(t: object, k: string | symbol): any;
declare function D4(t: typeof B, k: string): void;
declare const D5: any;
declare function D6(...a: unknown[]): number;
class B {
  @D1 a = 1;
  @D2 b = 2;
  @D2 c = 3;
  @D3 d = 4;
  @D4 static e = 5;
  @D4 f = 6;
  @D5 g = 7;
  @D6 h = 8;
  // @ts-expect-error
  @D3 i = 9;
  // @ts-expect-error
  @D1 j = 10;
}
export {};
