const cases = [{}, { a: 'x', b: 'y' }, { a: 'x' }];
for (const scope of cases) { const z: number = { ...scope }; }
