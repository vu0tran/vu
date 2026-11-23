// A parameter's type implied by its binding pattern: properties in the order of their names' bytes
function f({ zeta, alpha, mid }) { return 1; }
const x: number = f;
const g = ({ b, a = 1, c: { y, x } }) => 1;
const z: number = g;
function h([q, { s, r }]) { return 1; }
const w: number = h;
function k({ b, B, _a, a, Z, $x }) { return 1; }
const v: number = k;
