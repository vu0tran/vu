// x[k] = v with k not a literal, x made from {}: an assignment, not an expando declaration, so
// the file is typed
const hosts = {};
const raw = JSON.parse('{}');
for (const k of ['a', 'b']) {
  hosts[k] = raw.value;
}
export const first = raw.items[0];
export async function f() {
  await hosts;
}
