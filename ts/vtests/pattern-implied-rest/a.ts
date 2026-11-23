const A = ({ children, className = '', ...otherProps }) => {
  const n: number = otherProps;
  const m: string = children;
  return className;
};
const s: number = A({ children: 1, id: 'x' });
function B({ x, ...r }) { const q: number = r; return x; }
B({});
const C = ({ ...all }) => all;
const u: number = C({ a: 1 });
const v: string = u;
