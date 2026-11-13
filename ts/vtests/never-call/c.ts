declare function Service(): ClassDecorator;
declare function load(): Promise<number>;
@Service()
export class A {
  private isReady = false;
  async m1(): Promise<number> {
    try { return await load(); } catch (e) { this.handleError(e); }
  }
  async m2(x: string): Promise<number>;
  async m2(x: number): Promise<number>;
  async m2(x: string | number): Promise<number> {
    try { return await load(); } catch (e) { if (e instanceof Error) throw e; this.handleError(e); }
  }
  private handleError(e: unknown): never { throw new Error(String(e)); }
}
export class B {
  async m1(): Promise<number> {
    try { return await load(); } catch (e) { this.handleError(e); }
  }
  private handleError(e: unknown): never { throw new Error(String(e)); }
}
export {};
