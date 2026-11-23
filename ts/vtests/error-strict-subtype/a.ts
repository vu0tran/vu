import { R } from './missing';
declare const b: boolean;
function s() {
  if (b) return { n: 0, orders: [] };
  return { n: 1, orders: R.results };
}
export const z: number = s();
