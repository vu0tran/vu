new Promise((resolve, reject) => { resolve(1); resolve(2); });
const later = () => { resolve(3); resolve(4); };

function host(resolve) {
  new Promise((ok, fail) => {
    class K {
      m() { ok(1); ok(2); }
      get g() { fail(1); return fail(2); }
      static { ok(3); ok(4); }
      p = () => { ok(5); ok(6); };
    }
    const o = { m() { ok(7); ok(8); }, n: function () { fail(9); fail(10); } };
    ok(11);
    if (o) { ok(12); }
  });
  resolve(1); resolve(2);
}

new Promise(function named(resolve, reject) {
  void resolve();
  resolve?.();
  resolve.call(null);
  (resolve)();
  resolve(), reject();
  `${resolve()}`;
  tag`${reject()}`;
  x = resolve();
  await_like(resolve(), reject());
  new Thing(resolve());
  [resolve(), reject()];
  ({ a: resolve(), b: reject() });
  -resolve();
  typeof resolve() === "x";
});

new Promise(({ resolve }, [reject]) => { resolve(); resolve(); reject(); reject(); });
new Promise((resolve, ...rest) => { resolve(); rest[0](); resolve(); });
new Promise((resolve) => { const resolve2 = resolve; resolve2(); resolve(); { let resolve = f; resolve(); resolve(); } });
new Promise(async function* (resolve) { yield resolve(); yield resolve(); });
new Promise(async (resolve) => { for (const k in o) { resolve(k); } for await (const k of o) resolve(k); });
new Promise((resolve, reject) => {
  try { resolve(); a.b; } catch (e) { reject(e); } finally { resolve(); }
  try { resolve(); } catch { reject(); }
  try { foo(); resolve(); } catch { reject(); }
  try { resolve(foo()); } catch { reject(); }
  try { try { resolve(); x.y; } catch { reject(); } } catch { reject(); }
});
new Promise((resolve, reject) => {
  outer: for (;;) { inner: while (x) { if (y) continue outer; if (z) break inner; resolve(); } resolve(); break; }
  sw: switch (v) { case 1: resolve(); break sw; case 2: reject(); default: resolve(); }
});
new Promise((resolve, reject) => x ? resolve() : reject());
new Promise((resolve, reject) => (resolve(), reject()));
new Promise((resolve, reject) => { a ||= resolve(); b &&= reject(); c ??= resolve(); });
new Promise((resolve, reject) => { if (a) resolve(); else if (b) reject(); else { resolve(); } resolve(); });
new Promise((resolve) => setTimeout(resolve, 1)), new Promise((resolve) => { resolve(); resolve(); });
export default new Promise((resolve) => { resolve(); resolve(); });
new Promise((resolve) => { do { resolve(); } while (x); resolve(); });
new Promise((resolve) => { label: { resolve(); break label; } resolve(); });
new Promise((resolve) => { throw resolve(); });
new Promise((resolve) => { return resolve() && resolve(); });
new Promise((resolve) => { if (x) return resolve(); resolve(); });
new Promise((resolve) => { while (true) { resolve(); } });
new Promise(resolve => { for (let i = 0; i < n; i++) { if (i) { resolve(); } } resolve(); });
new Promise((resolve) => { function inner() { resolve(); } inner(); resolve(); resolve(); });
new Promise((resolve) => { resolve(); }, extra);
new Promise(resolver);
new window.Promise((resolve) => { resolve(); resolve(); });
new Promise(((resolve) => { resolve(); resolve(); }));
