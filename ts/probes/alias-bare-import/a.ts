// a type alias named bare through an import prints bare (a union or intersection of it)
import type { Unary, Either } from './lib';
declare const X: any;
declare function f1(p: Unary): void;
declare function f2(p: Either): void;
declare function f3(p: Either<number>): void;
f1(X); f2(X); f3(X);
