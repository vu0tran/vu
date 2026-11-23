// a declaration file's class named like a lib global var (and interface): a duplicate, the lib's
// declarations stay (@cloudflare/workers-types' ReadableStreamDefaultController beside the DOM lib's)
declare abstract class ReadableStreamDefaultController<R = any> {
  get desiredSize(): number | null;
  close(): void;
  enqueue(chunk?: R): void;
  error(reason: any): void;
}
