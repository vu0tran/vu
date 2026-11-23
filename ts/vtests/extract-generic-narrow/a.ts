// a type predicate to Extract<Union, { k: K }> with K generic: Extract's default constraint, the
// substitution type instantiated (U & member), and Extract members relate only as conditional types
export {};
type Task = { taskType: 'a'; x: number } | { taskType: 'b'; y: string } | { taskType: 'c'; z: boolean };
type Of<K extends Task['taskType']> = Extract<Task, { taskType: K }>;
function has<K extends Task['taskType']>(t: Task, k: K): t is Of<K> { return t.taskType === k; }
export function last<K extends Task['taskType']>(ts: Task[], k: K): Of<K> | null {
  let r: Of<K> | null = null;
  for (const t of ts) { if (has(t, k)) { r = t; const n: number = t; } }
  return r;
}
const q: number = last([], 'a');
