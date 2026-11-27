/* oxlint-disable no-debugger -- nothing here */
const a = 1;
/* oxlint-enable no-debugger */

/* oxlint-disable */
export const b = a;
/* oxlint-enable */

// eslint-disable-next-line no-debugger
export const c = 2;
/* eslint-disable no-console, no-debugger */
debugger;
/* eslint-enable no-console, no-debugger */
