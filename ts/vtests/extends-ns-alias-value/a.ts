declare class RealClient {
  x: number;
  once(e: string, f: () => void): this;
}
declare class RealPool {
  total: number;
}
declare const PG: { Client: typeof RealClient; Pool: typeof RealPool; Other: number };
declare namespace PG {
  type Client = RealClient;
  type Pool = RealPool;
  type Other = string;
  type Gone = RealPool;
}
class C extends PG.Client {
  readonly closed = new Promise<void>((resolve) => this.once('end', resolve));
}
class P extends PG.Pool {
  y = 1;
}
class O extends PG.Other {}
class G extends PG.Gone {}
const c = new C();
const s1: string = c.x;
const s2: string = c.closed;
const s3: string = new P().total;
const pt: PG.Pool = new P();
