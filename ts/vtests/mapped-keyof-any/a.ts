// a mapped type over keyof any, or keyof an unresolved name: a string index signature only
// (forEachMappedTypePropertyKeyTypeAndIndexSignatureKeyType)
import { SD } from './missing';
const m1: { [key in keyof any]: number } = {};
const n1: number = m1;
const m2: { [key in keyof SD]: (x: number) => string } = {};
const n2: number = m2;
const m4: { [key in keyof SD]?: string } = {};
const n4: number = m4;
const n5: boolean = Object.entries(m2);
