// an import of a package's untyped JavaScript that a pattern ambient module matches: the pattern
// module, before TS7016 (resolveExternalModule: patternAmbientModules before an untyped module)
import type { LanguageFn } from 'hl';
import bash from 'hl/lib/languages/bash';
const L: Record<string, LanguageFn> = { bash };
const n: string = bash;
void L; void n;
