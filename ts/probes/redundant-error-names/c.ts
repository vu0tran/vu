// an unresolved generic reference is named with its type arguments, as written
import * as gql from '@gql';
import { Maybe, Item } from '@gql';
import type { Same } from './b';
export type Wrapped = Maybe<Item>;
export interface L {
  a: gql.Maybe<string> | null;
  b: Maybe<gql.Item> | undefined;
  c: Maybe<Same> | null;
  d: gql.Maybe<Array<string>> | null;
  e: Wrapped | null;
}
