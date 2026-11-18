class G<T> { m() { this.y; } }
class H { m() { const s = this; s.y; } n(this: H) { this.y; } }
function f(this: { a: 1 }) { this.y; }
class A { x = 1; m() { this.y; } constructor() { this.z; } }
