type Op = '+' | '-';
export const ops: Record<Op, (l: any, r: any) => unknown> = Object.freeze({
  '+': (l, r) => l + r,
  '-': (l, r) => l - r,
});
