export interface Opts {
  depth: number;
}
export type Done = (err: Error | null) => void;
export interface Events {
  open: [name: string, ...rest: [opts?: Opts, done?: Done] | [done?: Done]];
  shut: [code: number, ...more: [Opts, Done] | string[]];
}
export interface Server {
  on<K extends keyof Events>(event: K, fn: (...args: Events[K]) => void): this;
  kind: string;
}
export interface Holder {
  configure?: (server: Server, opts: Opts) => void;
}
