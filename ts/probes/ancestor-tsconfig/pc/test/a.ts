// a file its nearest tsconfig leaves out, which the tsconfig above has: that program (ES2024: toSorted, findLast and with exist; Object.groupBy, Set#union and Iterator.from do not)
export const xs = [3, 1, 2].toSorted();
export const y = [1, 2].findLast((v) => v > 1);
export const g = Object.groupBy([1, 2], (v) => String(v));
export const s = new Set([1]).union(new Set([2]));
export const i = Iterator.from([1]);
export const w = [1, 2].with(0, 5);
