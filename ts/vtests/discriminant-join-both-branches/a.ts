export type Plan =
  | { action: 'a'; id: string | null }
  | { action: 'g'; url: string; id: string }
  | { action: 'u' };
declare const planOf: (a: boolean) => Plan;
declare const go: (u: string) => void;
export const s1 = (ok: boolean): string | null => {
  const plan = planOf(ok);
  if (plan.action === 'g') {
    go(plan.url);
  } else if (plan.action === 'u') {
    throw new Error('x');
  }
  return plan.id;
};
export const s2 = (ok: boolean): string | null => {
  let plan = planOf(ok);
  if (plan.action === 'u') plan = planOf(ok);
  if (plan.action === 'g') {
    go(plan.url);
  } else if (plan.action === 'u') {
    throw new Error('x');
  }
  return plan.id;
};
export const s3 = (ok: boolean): string | null => {
  const plan = planOf(ok);
  if (plan.action === 'g') {
  } else {
    const m: number = plan;
    if (plan.action === 'u') {
      throw new Error('x');
    }
    const n: number = plan;
  }
  const n: number = plan;
  return null;
};
export const s4 = (ok: boolean): string | null => {
  const plan = planOf(ok);
  if (plan.action === 'g') {
    const m: number = plan;
  } else {
    const m: number = plan;
  }
  const n: number = plan;
  return null;
};
export const s5 = (ok: boolean) => {
  const plan = planOf(ok);
  if (ok) {
  } else if (plan.action === 'u') {
    throw new Error('x');
  }
  const n: number = plan;
};
export const s6 = (plan: 'a' | 'g' | 'u') => {
  if (plan === 'g') {
  } else if (plan === 'u') {
    throw new Error('x');
  }
  const n: [typeof plan] = 0;
};
export const s7 = (x: string | number | boolean) => {
  if (typeof x === 'string') {
  } else if (typeof x === 'number') {
  } else {
    return;
  }
  const n: [typeof x] = 0;
};
