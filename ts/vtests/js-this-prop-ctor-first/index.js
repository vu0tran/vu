class Image {
  constructor() {
    this._src = "";
  }
  get src() {
    return this._src;
  }
  set src(value) {
    /** @type {number} */
    const n = value;
    this._src = value;
  }
  f() {
    /** @type {number} */
    const k = this.src;
  }
}
export { Image };
