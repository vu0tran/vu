class C {
  private handlers: { a?: (x: number) => void; b?: (s: string) => void } = {};
  private closed = false;
  report<K extends keyof typeof this.handlers>(event: K, run: (handler: NonNullable<(typeof this.handlers)[K]>) => void): void {
    if (this.closed && event !== 'a') return;
    const handler = this.handlers[event];
    if (handler !== undefined) run(handler);
  }
}
type H = { a?: (x: number) => void; b?: (s: string) => void };
function r2<K extends keyof H>(h: H, event: K, run: (handler: NonNullable<H[K]>) => void): void {
  const handler = h[event];
  if (handler !== undefined) run(handler);
}
export {};
