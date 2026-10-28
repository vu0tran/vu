// mandelbrot: a straight port of bench/mbt.c (one thread), printing the bitmap's MD5
const crypto = require('crypto');
function inside(cr, ci) {
  let zr = 0, zi = 0, tr = 0, ti = 0;
  for (let b = 0; b < 10; b++) {
    for (let k = 0; k < 5; k++) { zi = (zr + zr) * zi + ci; zr = tr - ti + cr; tr = zr * zr; ti = zi * zi; }
    if (tr + ti > 4.0) return false;
  }
  return true;
}
const size = Math.floor(((process.argv[2] ? parseInt(process.argv[2], 10) : 200) + 7) / 8) * 8, row = size / 8;
const inv = 2.0 / size;
console.log(`P4\n${size} ${size}`);
const px = new Uint8Array(size * row);
for (let y = 0; y < size; y++) {
  const ci = y * inv - 1.0;
  for (let x = 0; x < row; x++) {
    let byte = 0;
    for (let bit = 0; bit < 8; bit++) if (inside((x * 8 + bit) * inv - 1.5, ci)) byte |= 0x80 >> bit;
    px[y * row + x] = byte;
  }
}
console.log(crypto.createHash('md5').update(px).digest('hex'));
