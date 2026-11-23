type R = { required?: string; min?: number };
type P = { validation?: Omit<R, 'min'>; name: string };
export function f({ validation = {}, name }: P) {
  const n: number = validation;
  if (!validation.required) validation.required = 'x';
}
export const g = <T,>({ validation = {} }: { validation?: Omit<R, 'min'> & { t?: T } }) => { const n: number = validation; };
