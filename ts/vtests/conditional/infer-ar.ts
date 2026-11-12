export {};
type F = () => number;
type G = F extends () => infer R ? R : 0;
const g: G = 's';
type G2 = F extends (() => infer R) ? R : 0;
const g2: G2 = 's';
type G3 = (() => number) extends () => infer R ? R : 0;
const g3: G3 = 's';
