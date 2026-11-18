interface Base { signal?: AbortSignal; timeout?: number; tags?: string[]; stop?: string[] }
interface Cfg { timeout?: number; stop?: string[] }
interface Cfg2 { stop?: number }
declare function gen(o?: Cfg | undefined): void;
declare function gen2(o: Cfg2 | null): void;
export function f<O extends Base>(o: Omit<O, 'tags' | 'signal'>) {
  gen(o);
  gen2(o);
}
