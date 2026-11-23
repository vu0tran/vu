// require and module as the file's own names (const require = createRequire(...), (module) =>):
// not CommonJS, so the file is typed
const createRequire = (url) => (id) => ({ url, id });
const require = createRequire(import.meta.url);
const raw = JSON.parse('{}');
export const r = require.length;
export const names = ['a', 'b'].map((module) => module.toUpperCase() + raw.x);
for (const module of raw.list) {
  console.log(module.name);
}
export async function f() {
  await r;
}
