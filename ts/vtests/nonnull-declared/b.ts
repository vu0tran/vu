class B { w = 1; }
export class C1 extends B {
  constructor(private readonly f: () => number = () => this.w, private readonly g: number = 2) {
    super();
  }
}
export class C2 extends B {
  constructor() {
    const h = () => this.w;
    super();
    h();
  }
}
export class C3 extends B {
  constructor() {
    const q = this.w;
    super();
  }
}
