import type { EvName, Obs } from './b';

type Proc = (...args: any[]) => any;
interface Spy<T extends Proc = Proc> {
  mock: { calls: Parameters<T>[] };
}
export type TrackSpy = Spy<Obs['track']>;

export function find(spy: TrackSpy, ev: EvName<'sales'>, extra?: Record<string, unknown>): Parameters<Obs['track']> | undefined {
  return spy.mock.calls.find((call) => {
    const [cat, name, payload] = call;
    if (cat !== 'sales' || name !== ev) return false;
    if ((payload as Record<string, unknown> | undefined)?.x !== 1) return false;
    if (extra) {
      for (const [key, value] of Object.entries(extra)) {
        if ((payload as Record<string, unknown>)?.[key] !== value) return false;
      }
    }
    return true;
  });
}

export function plain(p: Parameters<Obs['track']>): unknown {
  const [, , d] = p;
  return d as Record<string, unknown>;
}
