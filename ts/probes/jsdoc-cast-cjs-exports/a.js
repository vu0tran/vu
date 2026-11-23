// @ts-check

const childProcess = /** @type {typeof import('child_process')} */ (require('child_process'));

/** @returns {boolean} */
const isOnLAN = () => {
  // Remote development instances run inside a VPC with production connectivity.
  const os = childProcess.execSync('uname -s').toString().trim();
  if (os === 'Linux') {
    return true;
  }

  const dns = childProcess.execSync('scutil --dns').toString();
  return dns.includes('10.253.');
};

exports.isOnLAN = isOnLAN;
