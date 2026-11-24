new Promise(async (resolve, reject) => {
  resolve();
});
function wrap() {
return new Promise((resolve, reject) => {
  if (resolve(a.b)) throw new Error();
  resolve(({ k: a.b, m() { resolve(); return import(m); } }));
});
}
