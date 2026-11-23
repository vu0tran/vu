declare class Comp<P = {}, S = {}> {
  constructor(props: P);
  props: Readonly<P>;
  state: S;
  setState(s: S): void;
}
