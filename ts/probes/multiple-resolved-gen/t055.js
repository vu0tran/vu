new Promise(function (resolve, reject) {
  resolve();
  if (o[k]) throw new Error();
});
function wrap() {
return new Promise((resolve, reject) => {
  resolve();
  resolve();
  return resolve(x);
});
}
const later = () => { resolve(); resolve(); };
