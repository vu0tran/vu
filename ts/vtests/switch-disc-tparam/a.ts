// switch (x.kind) where x has a type parameter member: its property through its constraint

type BillingContextError = {
  __typename: 'InvalidInputError' | 'NotFoundError';
  message: string;
};
export function expect<T extends { __typename: 'Ctx' }>(result: T | BillingContextError): T {
  switch (result.__typename) {
    case 'Ctx':
      return result;
    case 'InvalidInputError':
    case 'NotFoundError':
      const n: number = result;
      throw new Error(result.message);
    default: {
      result satisfies never;
      throw new Error('x');
    }
  }
}
export function g<T extends { kind: 'a'; v: number }>(r: T | { kind: 'b'; w: string }) {
  if (r.kind === 'a') {
    const x: string = r;
  } else {
    const y: number = r;
  }
}
