declare const args: [Date] | [number, string];
if (args.length === 1) { const [a] = args; const q: 'z' = a; }
if (args.length === 2) { const [a, b] = args; const q: 'z' = a; const r: 'z' = b; }
const [x] = args;
export const q: 'z' = x;
declare const t2: [1, 'a'] | [2, 'b', true?];
const [u, v] = t2;
export const qq: 'z' = u;
export const qv: 'z' = v;
if (args.length > 1) { const [a] = args; const q2: 'z' = a; }
