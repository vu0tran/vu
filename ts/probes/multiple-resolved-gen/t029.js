new Promise(async (resolve, reject) => {
  (new C()).p ? resolve(1) : reject(2);
  try {
    reject((class { p = x; q = () => new C(); }));
  } catch {
    var v7 = (class { p = reject(import(m)); q = () => y; });
    if (((z = 1) => z)) return;
  } finally {
    switch ([import(m), import(m)]) {
      case 1:
        if (a.b) {
          resolve(f() && x);
          resolve([new C(), new C()]);
          resolve(resolve(f()));
        } else {
          `t${(x ??= import(m))}u`;
          reject(h(a.b));
        }
        var v7 = f(() => `t${x}u`);
    }
  }
  reject(h(o[k]));
});
