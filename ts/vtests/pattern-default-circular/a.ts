// A binding element's default that reads an earlier name of the same pattern, while the pattern's
// types are being worked out: that name's type, not any (tsc types each binding element alone).
type AnswerSet = Record<string, string>;
declare function step(x: { a: AnswerSet; b: AnswerSet }): number;
export const m1 = ({ a, b = a }: { a: AnswerSet; b?: AnswerSet }) => step({ a, b });
export const m2 = ({ a, b = a }: { a: AnswerSet; b?: AnswerSet }) => {
  const n: number = [a, b];
};
export const m3 = ({ a, b = a }: { a?: AnswerSet; b?: AnswerSet }) => step({ a: {}, b });
