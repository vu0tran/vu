declare const fl: FileList;
export const n1: number = fl[Symbol.iterator];
const ys = [...fl];
export const n2: number = ys;
