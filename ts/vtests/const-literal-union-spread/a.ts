// A union spread in a const object literal (a package's naturalLanguageSearch, ...(m ? { market: m } : {})):
// the literal once for each member, united (getSpreadType maps over the union).
declare const m: string | undefined;
export const base = {
  bounded: false,
  ...(m ? { market: m } : {}),
  trigger: 'INITIAL_SUBMIT',
} as const;
const n1: number = base.bounded;
const n3: number = base.market;
