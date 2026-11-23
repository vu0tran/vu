// a package's relative /// <reference types="./types/global" /> (next's index.d.ts): its file loaded,
// with the declare module '*.module.css' a CSS module import resolves to
import type { Meta } from 'nx';
import styles from './x.module.css';
export const m: Meta = { title: 'a' };
export const s: number = styles.foo;
