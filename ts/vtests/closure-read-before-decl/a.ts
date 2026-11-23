// a function in a const read above its declaration, in a narrowed branch (permits' worker.ts
// checkEligibility): its body's flow is its declaration's, not the narrowings where it was read
type A = { authMode: 'shared-proxy'; url: string };
type B = { authMode: 'native-oidc'; rbac: { user: string } };
declare function mk(o: object): void;
export function make(config: A | B) {
  mk({
    a: 1,
    ...(config.authMode === 'shared-proxy' ? { f: () => check() } : {}),
  });
  const check = () => {
    if (config.authMode === 'shared-proxy') return 1;
    const g: number = config.rbac;
    return g;
  };
}
export function make2(config: A | B) {
  if (config.authMode === 'shared-proxy') later();
  function later() {
    if (config.authMode === 'shared-proxy') return 1;
    const g: number = config.rbac;
    return g;
  }
}
export function make3(config: A | B) {
  mk({ ...(config.authMode === 'shared-proxy' ? { f: () => check3() } : {}) });
  const check3 = async (): Promise<number> => {
    if (config.authMode === 'shared-proxy') return 1;
    const g: number = config.rbac;
    return g;
  };
}
