class K {
  t?: { close(): void; u: number } | string;
  go() {
    try {
      this.t = { close() {}, u: 1 };
      this.t.u;
    } catch (e) {
      const z: 'z' = this.t;
      if (this.t && typeof this.t !== 'string') this.t.close();
    }
  }
}
export { K };
