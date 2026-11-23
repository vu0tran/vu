// a package's interface whose base names nothing: no base (skipLibCheck hides tsc's error)
import type { Feature } from 'geo-pkg';
declare const f: Feature;
const s: number = f.source;
const g: number = f.geometry;
