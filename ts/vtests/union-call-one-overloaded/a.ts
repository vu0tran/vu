interface Cmd<I, O> { input: I; _o?: O }
class GetCmd implements Cmd<{ k: string }, { Body?: string; Len: number }> {
  input = { k: "" };
}
interface Opts { abortSignal?: AbortSignal; retries?: number }
declare class Client {
  send<I extends object, O extends object>(command: Cmd<I, O>, options?: Opts): Promise<O>;
  send<I extends object, O extends object>(command: Cmd<I, O>, cb: (err: any, data?: O) => void): void;
  send<I extends object, O extends object>(command: Cmd<I, O>, options: Opts, cb: (err: any, data?: O) => void): void;
}
type Ops = {
  send: (command: GetCmd, options?: { abortSignal?: AbortSignal }) => Promise<{ Body?: string | null; Extra?: number }>;
};
declare const ov: ((r: string) => Ops) | null;
export async function f() {
  const client = ov ? ov("x") : new Client();
  const a = new AbortController();
  const object = await client.send(new GetCmd(), { abortSignal: a.signal });
  const n: number = object;
  const b: number = object.Body;
  const s: number = client.send;
  client.send(new GetCmd(), (err) => {});
  client.send(new GetCmd(), {}, (err, d) => { const z: number = d; });
}
export async function g() {
  const client = new Client() as Ops | Client;
  const object = await client.send(new GetCmd());
  const n: number = object;
}
declare const h: ((a: { x: 1 }) => Promise<{ a: 1; b: 1 }>) | ((a: { y: 1 }) => Promise<{ a: 1 }>);
const hr: number = h({ x: 1, y: 1 });
declare const h2: (<T>(a: T, b: { x: 1 }) => T) | ((a: string, b: { y: 1 }) => number);
const hr2: boolean = h2("s", { x: 1, y: 1 });
declare const h3: ((a: string, b: { y: 1 }) => number) | (<T>(a: T, b: { x: 1 }) => T);
const hr3: boolean = h3("s", { x: 1, y: 1 });
