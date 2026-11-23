interface Cmd<I, O> { input: I; output: O }
declare class Get implements Cmd<{ k: string }, { body: string }> {
  input: { k: string };
  output: { body: string };
}
declare function send<I, O>(c: Cmd<I, O> & Get): O;
const r1: number = send(new Get());
declare function q<T>(a: T & "x"): T;
const r2: boolean = q("x");
const r3 = q("x");
const r4: number = r3;
declare function w<T>(a: T & { n: 1 }): T;
const r5: number = w({ n: 1, m: 2 });
