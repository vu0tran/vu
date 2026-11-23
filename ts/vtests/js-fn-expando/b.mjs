export function wrap() {
  function setHeader(/** @type {string} */ name) {
    return name.length;
  }
  setHeader.marked = true;
  setHeader.count = 1;
  return setHeader;
}
