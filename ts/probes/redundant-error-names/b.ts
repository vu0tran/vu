// aliases of unresolved names in another file
import { graphql, Named, Other } from '@gql';
export const Doc = graphql('q');
type ResultOf<T> = T extends { __r?: infer R } ? R : never;
export type Loan = NonNullable<ResultOf<typeof Doc>['x']>;
export type Same = Named;
export type Picked = Other['x'];
export type Both = Named & { k: 1 };
