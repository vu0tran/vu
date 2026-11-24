export type Kind = 'first' | 'second';

export class Holder<T extends Kind = 'first'> {
  readonly kind: T;
  constructor(name: string, kind: T = 'first' as T) {
    this.kind = kind;
    void name;
  }
}

export class Plain<T extends Kind = 'first'> {
  readonly kind: T | undefined;
  constructor(name: string) {
    void name;
  }
}
