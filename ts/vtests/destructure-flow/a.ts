interface Cov { enabled?: boolean; provider?: string }
interface Cfg { test?: { coverage?: Cov; name: string | undefined } }
declare const cfg: Cfg;
if (cfg.test?.coverage) {
  const { coverage } = cfg.test;
  coverage.enabled = true;
}
if (cfg.test && cfg.test.name) {
  const { name } = cfg.test;
  const n: string = name;
  let { name: n2 } = cfg.test;
  n2 = n;
}
export {};
