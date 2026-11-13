type JE<P extends object> = P & { version: number };
class S<P extends object> {
  m(results: (JE<P> | null)[], entries: Map<string, JE<P>>) {
    results.forEach((entry, idx) => {
      if (entry) entries.set("a", entry);
    });
    for (const e of results) { if (e) { const v: string = e.version; } }
  }
}
function g<P extends object>(e: JE<P> | null) { if (e) { const v: string = e; } else { const w: number = e; } }
function h<P>(e: P | null) { if (e) { const v: string = e; } }
export {};
function k2<P extends object>(e: (P & { b: 1 }) | undefined) { if (!e) { const v: number = e; } else { const w: number = e; } }
