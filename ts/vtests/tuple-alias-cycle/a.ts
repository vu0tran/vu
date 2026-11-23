// a tuple alias whose element reaches back to the union alias that holds it (@smithy/types'
// $Schema / $MemberSchema / $SchemaRef): the tuple exists before its elements are made, so
// neither alias silently becomes the error type, whichever is resolved first
export {};
type IsNever<T> = [T] extends [never] ? "never" : 0 extends 1 & T ? "any" : "other";
type B = [A];
type A = number | B;
const q0: IsNever<B> = 3;
const q1: IsNever<A> = 3;
type Member = [SRef, number];
type S = "unit" | number | Member;
type SRef = S | (() => S);
const q2: IsNever<SRef> = 3;
const q3: IsNever<S> = 3;
const q4: IsNever<Member> = 3;
