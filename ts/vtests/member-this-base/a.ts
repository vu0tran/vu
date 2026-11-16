interface Span { setAttribute(key: string, value: number | undefined): this; end(): void; isRecording(): boolean }
export class EmptySpan implements Span {
  setAttribute(): this { return this; }
  end(): void {}
  isRecording(): boolean { return false; }
}
interface Chain { next(): this; val: number }
export class C1 implements Chain { val = 1; next(): C1 { return this; } }
class B0 { me(): this { return this; } }
export class B1 extends B0 { me(): this { return this; } }
export class B2 extends B0 { me(): B0 { return this; } }
