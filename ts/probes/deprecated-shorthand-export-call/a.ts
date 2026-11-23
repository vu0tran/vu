import { agent, escalate, tasks, viaAlias } from './m';
viaAlias(1);
declare const overloaded: {
  (a: string): string;
  /** @deprecated Number overload. */
  (a: number): number;
};
overloaded(1);
overloaded('x');

declare function createResolver<T>(name: string, r: T): T;
declare function untyped(name: string, r: object): void;

export const r1 = createResolver('X', {
  agent,
  tasks,
});
untyped('Y', { escalate, agent });
export const r3 = { tasks };
export const r4 = { t: tasks };

/** @deprecated Use the other one. */
const localOld = 1;
const localNew = 2;
export { localOld, localNew };
export { localOld as renamedOld };
export { tasks as reTasks, agent as reAgent } from './m';
export { escalate } from './m';
export type { Fn2 } from './m';

declare class Err {
  constructor(message: string, options?: { path?: string[] });
  /** @deprecated Please use the options overload instead. */
  constructor(message: string, nodes?: unknown, source?: unknown, positions?: unknown, path?: string[]);
}
export const e1 = new Err('m', undefined, undefined, undefined, ['x']);
export const e2 = new Err('m', { path: [] });

declare class Page {
  /** @deprecated Use other. */
  waitForSelector(s: string): void;
  goto(s: string): void;
}
declare const page: Page;
(page as { waitForSelector: typeof page.waitForSelector }).waitForSelector = (s: string) => undefined;
export type G = typeof page.goto;
