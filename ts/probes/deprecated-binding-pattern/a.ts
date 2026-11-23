import { ok } from 'cf:test';
export async function f() {
  const { env: testEnv } = await import('cf:test');
  const { env } = await import('cf:test');
  const m = await import('cf:test');
  m.SELF();
  return [testEnv.a, env.a, ok];
}
export async function g() {
  const { SELF } = await import('cf:test');
  SELF();
}
