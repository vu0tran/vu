interface CE { A: string; D: 'x' | 'y'; R?: 'false'; P?: number }
type Env = Omit<CE, 'A' | 'D'> & { D: 'x' | 'y' | 't'; A?: string; Q?: number };
type TestEnv = Omit<CE, 'P' | 'Q' | 'R'> & { P: number; Q: number; R?: string };
declare const t: TestEnv;
export const e: Env = t;
type Env2 = Omit<CE, 'A'> & { A?: string };
type T2 = Omit<CE, 'R'> & { R?: string };
declare const t2: T2;
export const e2: Env2 = t2;
declare const t3: { R?: string };
export const e3: Omit<CE, 'A' | 'D'> = t3;
