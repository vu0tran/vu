export {};
type G9 = ((cb: number) => void) extends ((onfulfilled: infer F) => any) ? 1 : 0;
const g9: G9 = 5;
type G10 = ((cb: number) => void) extends ((onfulfilled: number) => any) ? 1 : 0;
const g10: G10 = 5;
type G11 = (() => number) extends (() => infer R) ? R : 0;
const g11: G11 = 's';
type G12 = ((cb: number) => void) extends ((onfulfilled: infer F) => void) ? F : 0;
const g12: G12 = 's';
