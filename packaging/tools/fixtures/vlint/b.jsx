const list = [1, 2, 3];
export const View = () => <ul>{[...[...list]].map((n) => <li key={n}>{n}</li>)}</ul>;
for (let i = 0; i < 10; i--) {}
