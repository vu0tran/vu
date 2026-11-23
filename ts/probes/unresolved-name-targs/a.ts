import { Resp, Req } from './missing';
import * as gql from './missing2';
declare const X: any;
declare function getter<A, B, C>(f: (data: B) => C, g: (a: A) => B): void;
getter<Req, Resp, gql.Maybe<gql.Out>>(X, X);
declare function h(p: gql.Maybe<gql.Out>[]): void;
h(X);
declare function k(p: Resp[]): void;
k(X);
