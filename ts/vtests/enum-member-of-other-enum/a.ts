import { Gen as G } from './gen';
export enum Ev { Created = G.TaskCreated, Updated = G.TaskUpdated, Num = G.N }
const a: 'TASK_CREATED' = Ev.Created;
const b: 'x' = Ev.Updated;
const c: number = Ev.Num;
const r: Record<Ev, string> = { [Ev.Created]: 'a', [Ev.Updated]: 'b', [Ev.Num]: 'c' };
const d: boolean = r;
