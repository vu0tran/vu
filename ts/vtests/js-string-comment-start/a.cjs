// @ts-check
// a /** inside a string, a template or a regular expression starts no comment: '@playwright' isn't a tag
const B = [
  {
    dependencies: ['@biomejs/**', `x/**`, 'tslint'],
    label: 'Use @playwright/test',
    re: /[/**]/, s: "@a",
  },
];
/** @type {number} */
const x = B;
module.exports = x;
