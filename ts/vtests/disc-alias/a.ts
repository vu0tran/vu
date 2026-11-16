type Cred = { host: string } & ({ auth: 'password'; pw: string } | { auth: 'key'; key: string });
export function f(c: Cred): string {
  const { auth, host } = c;
  if (auth === 'password') return c.pw + host;
  return c.key;
}
export function g(c: Cred): string {
  const a = c.auth;
  return a === 'key' ? c.key : c.pw;
}
export function h(c: Cred): string {
  let { auth } = c;
  if (auth === 'password') return c.pw;
  return '';
}
