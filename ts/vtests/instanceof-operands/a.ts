// instanceof with any on the right (an unresolved import): no narrowing
import { AuthError } from 'nope-module';
declare const Anyc: any;
export function f(error: unknown, e2: string | number) {
  if (!(error instanceof AuthError)) return false;
  const x: number = error;
  return true;
}
