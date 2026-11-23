// as extract-generic-narrow, the union's members made by a generic function from a package's mapped
// types: their mappers' entries for that function's type parameters aren't type arguments of them
import { lit, obj, union, num, type infer as Infer } from 'pk';
const base = obj({ id: num });
const taskFor = <TaskType extends 'a' | 'b'>(t: TaskType) => base.extend({ taskType: lit(t), v: num });
const s = union([taskFor('a'), taskFor('b')]);
type Task = Infer<typeof s>;
type Of<K extends Task['taskType']> = Extract<Task, { taskType: K }>;
function has<K extends Task['taskType']>(t: Task, k: K): t is Of<K> { return t.taskType === k; }
export function last<K extends Task['taskType']>(ts: Task[], k: K): Of<K> | null {
  let r: Of<K> | null = null;
  for (const t of ts) { if (has(t, k)) { r = t; const n: number = t; } }
  return r;
}
const q: number = last([], 'a');
