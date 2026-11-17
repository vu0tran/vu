export {};
type ScanState = 'code' | 'single' | 'double' | 'template' | 'block-comment';

/**
 * Advance a lexical scan over one line of generated code. Only template-literal
 * content lines must keep their exact text, but a backtick inside a quoted
 * string or a comment must not be mistaken for a template boundary.
 */
function scanLine(line: string, state: ScanState): ScanState {
	for (let i = 0; i < line.length; i++) {
		const ch = line[i];
		switch (state) {
			case 'code':
				if (ch === "'") state = 'single';
				else if (ch === '"') state = 'double';
				else if (ch === '`') state = 'template';
				else if (ch === '/' && line[i + 1] === '*') {
					state = 'block-comment';
					i++;
				} else if (ch === '/' && line[i + 1] === '/') {
					return state;
				}
				break;
			case 'single':
			case 'double':
			case 'template': {
				if (ch === '\\') {
					i++;
				} else if (
					(state === 'single' && ch === "'") ||
					(state === 'double' && ch === '"') ||
					(state === 'template' && ch === '`')
				) {
					state = 'code';
				}
				break;
			}
			case 'block-comment':
				if (ch === '*' && line[i + 1] === '/') {
					state = 'code';
					i++;
				}
				break;
		}
	}
	// Quoted strings cannot span lines; only templates and block comments carry over.
	return state === 'single' || state === 'double' ? 'code' : state;
}

const q: number = scanLine("a", "code");
