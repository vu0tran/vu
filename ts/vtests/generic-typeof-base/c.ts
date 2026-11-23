type RO<T> = { required?: string; min?: T };
type CP<T> = { rules?: Omit<RO<T>, 'min'>; name: string };
type P<T> = { validation?: CP<T>['rules']; name: string };
export function f<T>({ validation = {}, name }: P<T>) {
  const n: number = validation;
  if (!validation.required) validation.required = 'x';
}
