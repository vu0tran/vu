// the quiet pass for a function in a pending initializer runs when it mentions the variable or reads
// this: a literal's method reading this inside Object.assign(...) in its own const's initializer
declare class EventEmitter { on(e: string, f: () => void): this }
export function fake() {
  const p = Object.assign(new EventEmitter(), {
    kills: [] as string[],
    kill(signal: string) {
      this.kills.push(signal);
      const n: number = this.kills;
      return true;
    },
  });
  return p;
}
