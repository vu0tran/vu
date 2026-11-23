// A function whose return type is inferred while another variable's type is being found, and
// which mentions it: its body is checked once the outermost one has its type, not before.
const des = (x: number) => {
  return { ...pop(x) };
};
const pop = (x: number) => {
  const out: Record<string, any> = {};
  const v: number = des(x);
  [1].forEach((k) => {
    const w: number = des(k);
  });
  return out;
};
const selfF = (x: number) => {
  const v: string = selfF(x);
  return x;
};
