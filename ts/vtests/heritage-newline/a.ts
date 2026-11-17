export {};
class N<A extends string> { a!: A }
class T<A extends string> extends N<A>
{ x = 1 }
const q: number = new T<"a">().a;
class U<B> extends Array<B>
{}
const u: string = new U<number>()[0];
