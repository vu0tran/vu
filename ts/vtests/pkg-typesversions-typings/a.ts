// typesVersions maps the package's typings path (mom.d.ts -> ts3.1-typings/mom.d.ts), not
// "index"
import { fresh, type In } from 'mom';
export const f: string = fresh;
export const i: number = null as unknown as In;
