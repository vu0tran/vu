// typeof x.a: x's narrowed type where the query is, and not nullish inside an optional chain on x
interface Task { runs: { at: number }[] }
declare const task: Task | null;
const latest = task?.runs.reduce<(typeof task.runs)[number] | undefined>((l, r) => r, undefined);
const n1: number | undefined = latest?.at;
interface Cl { pricing(x: number): string }
let client: Cl | null = null;
function setup() {
  client = { pricing: (x) => 's' };
  const p: typeof client.pricing = (x: number) => 's';
  const q: number = p;
}
export {};
