class W { n = 1; close(): void {} }
export class T {
  private ws: W | null = null;
  a(): number { if (this.ws) { this.ws = null; return this.ws.n; } return 0; }
  b(): void { if (this.ws) { [1].forEach(() => this.ws.close()); } }
  c(): number { if (!this.ws) return 0; const f = function (this: T) { return this.ws.n; }; return f.call(this); }
  d(): number { if (this.ws !== null) return this.ws.n; return 0; }
  e(): number { return this.ws?.n ?? 0; }
  g(o: T): number { if (this.ws) return o.ws.n; return 0; }
  static s: W | null = null;
  static h(): number { if (this.s) return this.s.n; return 0; }
}
