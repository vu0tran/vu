import A, { B, C } from 'lib2';
import own from 'lib';
import * as l2 from 'lib2';
console.log(A, B, C, own, l2.A, l2.B, l2.default, l2.C);
export { A as default, B };
export * from 'lib2';
export { Icon, nothing } from 'lib';
