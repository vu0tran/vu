import { add, type Pair } from './util/math.js';
import { greet } from './util/greet.js';
import chalk from 'chalk';

const p: Pair = [1, 2];
console.log(chalk.green(greet('knip')), add(...p));
