// A class's set accessor parameter without a type: the get accessor's return type.
class Img {
  _src = "";
  get src() {
    return this._src;
  }
  set src(value) {
    const n: number = value;
    this._src = value;
  }
}
class J {
  _s: number = 1;
  get s(): number { return this._s; }
  set s(v) { const n: string = v; }
  static get t() { return true; }
  static set t(v) { const n: string = v; }
}
const o = { get a() { return 1n; }, set a(v) { const n: string = v; } };
