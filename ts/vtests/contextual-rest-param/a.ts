declare let op: (url?: string | URL, target?: string, features?: string) => number;
op = (...args) => { const z: boolean = args; return 1; };
declare let op2: (a: string, b?: number) => number;
op2 = (...args) => { const z: boolean = args; return 1; };
const f3: (a: string, ...r: number[]) => void = (...xs) => { const z: boolean = xs; };
