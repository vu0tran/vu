// typeof this in an instance member's signature: the class's this type.
export class Bloom {
  bits: number[] = [];
  export(): { bits: number[] } {
    return { bits: this.bits };
  }
  import(data: ReturnType<(typeof this)['export']>): void {
    void data;
  }
  same(other: typeof this): typeof this {
    return other;
  }
}
const b = new Bloom();
b.import({ bits: [1] });
b.import({ bits: ['x'] });
const n: number = b.same(b);
class Sub extends Bloom {
  extra = 1;
}
const s = new Sub();
const e: string = s.same(s).extra;
