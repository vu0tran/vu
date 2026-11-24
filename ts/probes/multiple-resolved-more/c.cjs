new Promise(function (resolve) {
  with (o) { resolve(); }
  resolve();
  with (o) resolve(), resolve();
});
new Promise(function (resolve) {
  resolve();
  var resolve = 1;
  resolve();
});
