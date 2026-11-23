import { setTimeout } from './c';
export async function f() {
  await setTimeout(20);
  globalThis.setTimeout('x', 1);
}
