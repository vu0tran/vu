declare module 'ev' {
  class E<T = number> { v: T; constructor(x?: string); }
  import internal = require('ev');
  namespace E {
    export { internal as E };
  }
  export = E;
}
