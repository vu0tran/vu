export class K {
  private handlers: { a?: (x: number) => void; b?: (s: string) => void } = {};
  keys: Array<keyof typeof this.handlers> = ['a'];
  report<P extends keyof typeof this.handlers>(k: P, run: (h: NonNullable<(typeof this.handlers)[P]>) => void) { return [k, run]; }
  t() { this.report('a', (h) => { const z: 'z' = h; }); const y: 'z' = this.keys; }
}
