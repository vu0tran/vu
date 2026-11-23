// a namespace import of a missing module: its generic names resolve to nothing
import * as gql from '@gql';
type Maybe<T = string> = T | null;
export function f(a: gql.Maybe<string>, b: Maybe<string>): gql.Maybe<gql.Item<number>> {
  return a ?? b?.length ?? a.x;
}
