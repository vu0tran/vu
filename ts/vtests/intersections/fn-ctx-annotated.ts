type F1 = (this: { n: number }, r: any, ...e: any[]) => { pass: boolean };
type F2 = (this: { n: number }, r: any, ...e: [x: string]) => { pass: boolean };
declare function ext(m: Record<string, F1 & F2>): void;
ext({ m(this: { n: number }, a: any, b: string) { return { pass: this.n > 0 && b === 'x' }; } });
ext({ k(this: { n: number }, a: any, b: string) { return { pass: 1 }; } });
