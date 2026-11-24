export interface Payload {
  /**
   * @deprecated use newId
   */
  oldId: string;
  newId: string;
}

export function send(p: Payload): void {
  void p;
}

send({ oldId: 'a', newId: 'b' });

export function track<K extends 'one' | 'two'>(kind: K, p: K extends 'one' ? Payload : { other: number }): void {
  void kind;
  void p;
}

track('one', { oldId: 'a', newId: 'b' });

type Init<T> = { [P in keyof T]?: T[P] };
export function init(p: Init<Payload>): void {
  void p;
}
init({ oldId: 'x' });

type Cases = { case: 'a'; value: Init<Payload> } | { case: 'b'; value: { z: number } };
type ValueOf<C extends Cases['case']> = Extract<Cases, { case: C }>['value'];
export function emit<C extends Cases['case']>(c: C, v: ValueOf<C>): void {
  void c;
  void v;
}
emit('a', { oldId: 'y' });
