export class T {
  text: string | null = null;
  n: number | undefined;
  o: { a: string | number } = { a: 1 };
  run(xs: string[]) {
    if (this.text === null) throw new Error('x');
    const snap = this.text;
    for (let i = 0; i < xs.length; i++) {
      const n: number = this.text.length;
      if (n === 0) { this.text = snap; continue; }
      this.text = this.text + xs[i];
      if (n > 3) this.text = null;
    }
    const z: string = this.text;
    this.n = 1;
    while (this.n < 10) { this.n = this.n + 1; if (this.n > 5) this.n = undefined; }
    const q: number = this.n;
    this.o.a = 'x';
    for (const x of xs) { const w: string = this.o.a; this.o.a = 2; }
  }
}
