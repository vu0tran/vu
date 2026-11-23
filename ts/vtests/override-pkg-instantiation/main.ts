import { Base, type Cfg, type Kinds, type ST } from 'pk';
// the derived method's parameter is the base's, instantiated with P's Types: the same type
export class P<Types extends ST> extends Base<Types> {
  override on(c: Cfg<Types, Kinds>) { const k: number = c.kind; return c; }
}
const n: number = 's';
