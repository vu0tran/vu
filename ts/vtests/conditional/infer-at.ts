export {};
type G7 = { then(cb: (v: string) => void): void } extends { then(onfulfilled: infer F): any } ? F : 0;
const g7: G7 = 5;
type G8 = { then: (cb: (v: string) => void) => void } extends { then: (onfulfilled: infer F) => any } ? F : 0;
const g8: G8 = 5;
type G9 = { x: string } extends { x: infer F } ? F : 0;
const g9: G9 = 5;
