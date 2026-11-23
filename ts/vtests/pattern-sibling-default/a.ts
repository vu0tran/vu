interface Prov { defaultLabel: string; idPrefix: string }
type FC<P> = (props: P) => string;
export const B: FC<{ label?: string; provider: Prov }> = ({ provider, label = provider.defaultLabel }) => {
  const ok = provider.idPrefix === "x";
  const n: number = label;
  return label + String(ok);
};
declare function g(f: (p: { provider: Prov; label?: string }) => string): void;
g(({ provider, label = provider.defaultLabel }) => {
  const ok = provider.idPrefix;
  const n: number = label;
  return label + ok;
});
