// any isn't narrowed by equality with a literal (narrowTypeByEquality returns it); instanceof
// and typeof do narrow it.
declare const record: any;
declare function f(o: { a: 'X' | 'Y' }): void;
const outcome = record.agentOutcome;
if (outcome === 'X' || outcome === 'Y') {
  const n: number = outcome;
  f({ a: outcome });
}
const o2: any = record.b;
if (o2 === 'X') {
  const n2: number = o2;
}
if (o2 !== 1) {
  const n2b: number = o2;
} else {
  const n2c: string = o2;
}
switch (o2) {
  case 'Z': {
    const n3: number = o2;
  }
}
if (o2 instanceof Date) {
  const n5: number = o2;
}
if (typeof o2 === 'string') {
  const n6: number = o2;
}
export {};
