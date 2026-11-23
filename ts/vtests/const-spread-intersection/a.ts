type Campaign = {
  id: string;
  link: { label: string; href: string };
  variant?: number;
  linkStyle?: 'text' | 'button';
  include: readonly string[];
} & ({ startsAt: string; expiresAt: string } | { startsAt?: never; expiresAt?: never });
const campaign: Campaign = {
  id: 'x',
  link: { label: 'a', href: '/b' },
  variant: 1,
  startsAt: '2020',
  expiresAt: '2100',
  include: ['/'],
};
const campaigns = {
  text: { ...campaign, linkStyle: "text" },
  button: { ...campaign, linkStyle: "button" },
} as const;
const n1: number = campaigns;
const n2: number = campaigns.text;
declare const both: { a: 1 } & { b: string };
const o3 = { ...both, c: 2 } as const;
const n4: number = o3;
