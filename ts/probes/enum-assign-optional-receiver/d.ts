import { Phone1 as P1 } from './e1';
import { Phone1 as P2 } from './e2';

type Labels = { [k in P1]: string };
export const labels: Labels = { [P1.Home]: 'h', [P1.Mobile]: 'm' };
declare const v: P2;
export const z1 = labels[v];
declare const items: Array<{ t: P2 }>;
export const z2 = items.map((i) => labels[i.t]);
declare const r: { items: Array<{ t: P2 }> } | null | undefined;
export const z3 = r?.items.map((i) => labels[i.t]);
export const labels2: Record<P1, string> = { [P1.Home]: 'h', [P1.Mobile]: 'm' };
export const z4 = labels2[v];
