// a TypeScript config: knip loads it with jiti; vknip through node
import type { KnipConfig } from 'knip';

const config: KnipConfig = {
  entry: ['src/index.ts'],
  project: ['src/**/*.ts'],
  ignoreDependencies: ['picocolors'],
};

export default config;
