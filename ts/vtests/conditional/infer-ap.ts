export {};
interface P2<T> { then(cb: (v: T) => void): void }
type G5 = P2<string> extends { then(onfulfilled: any): any } ? 1 : 0;
const g5: G5 = 5;
type G6 = P2<string> extends { then: (onfulfilled: infer F) => any } ? F : 0;
const g6: G6 = 5;
type G7 = { then(cb: (v: string) => void): void } extends { then(onfulfilled: infer F): any } ? F : 0;
const g7: G7 = 5;
type G8 = ((cb: number) => void) extends ((onfulfilled: infer F) => any) ? F : 0;
const g8: G8 = 's';
