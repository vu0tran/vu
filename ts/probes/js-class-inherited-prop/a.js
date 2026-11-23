// this.x = v at the top of a JavaScript class's constructor, x inherited: x is v's type (the
// base's type only where it isn't assigned), getFlowTypeOfProperty
import { Base } from './b.js';
const raw = JSON.parse('{}');
export class X extends Base {
  constructor(p) {
    super(p);
    this.state = { filter: '', rules: [raw.r] };
    this.wide = { a: '' };
  }
  async m() {
    await this.state.filter;
    await this.wide.a;
    return this.state.rules[0].name;
  }
}
