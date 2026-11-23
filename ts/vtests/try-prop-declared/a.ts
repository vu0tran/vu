// A property not narrowed before a try block, assigned in a loop in it: the declared type in the
// catch and finally blocks (their start's union has it, which takes every assignment's).
declare function next(): { doc: string } | null;
declare function ret(m: string): Promise<boolean>;
export class W {
  sticky: string | null = null;
  stopping = false;
  async run(): Promise<void> {
    try {
      do {
        if (this.stopping) break;
        while (!this.stopping) {
          const job = next();
          if (!job) break;
          if (this.sticky && job.doc !== this.sticky) await ret(this.sticky);
          this.sticky = job.doc;
        }
      } while (!this.stopping);
    } finally {
      const a: number = this.sticky;
      if (this.sticky) {
        const n: number = this.sticky;
      }
    }
  }
  async run2(): Promise<void> {
    try {
      for (const x of ['a', 'b']) this.sticky = x;
    } catch {
      const c: number = this.sticky;
    }
  }
}
