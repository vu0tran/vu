// const x = {} in JavaScript: x.p = v in the same function declares p, typed by what's assigned
function parseArgs(argv) {
  const opts = {};
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--name') opts.name = argv[++i];
    else if (a === '--count') opts.count = Number(argv[++i]);
    else if (a === '--flag') opts.flag = true;
  }
  return opts;
}
export async function main() {
  const o = parseArgs(process.argv);
  await o.count;
  await o.flag;
  return o.name.trim();
}
const top = {};
top.label = 'x';
export const len = top.label.length;
export async function f() {
  await top.label;
}
