new Promise(function (resolve, reject) {
  resolve();
  try {
    setTimeout(function () {
      var v5 = h(import(m));
      if (o[k]) throw new Error();
      resolve();
    });
  } catch {
    if ((class { p = import(m); q = () => o[k]; })) return;
  } finally {
    for (let j = 0; j < n; j++) {
      switch (f(() => o[k])) {
        case 1:
          reject(x);
          var v1 = (x).p && f(() => import(m));
          break;
      }
      B3: {
        while (y || o[k]) {
          `t${((z = import(m)) => z)}u`;
          var v6 = reject((x ??= y));
        }
        fn((err, val) => {
          resolve((x ??= import(m)));
          new C();
          ((z = (a.b ? x : f())) => z);
        });
        if (({ k: o[k], m() { resolve(); return a.b; } })) break B3;
      }
      return import(m);
    }
  }
  try {
    var v8 = ((z = (o[k] ? f() : f())) => z);
  } catch (e) {
    [a.b, o[k]] ? resolve(1) : reject(2);
    resolve(f());
  }
});
