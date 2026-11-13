export const site = {
  name: 'ShareCatalog',
  version: '0.1.0',
  repository: 'https://github.com/tidus747/sharecatalog',
  description:
    'Turn indexed files into an editable document catalog with SharePoint links. Built for Windows, ready for Confluence.',
};

export function url(path = ''): string {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  return `${base}/${path.replace(/^\//, '')}`;
}

export const navigation = [
  {
    label: 'Start here',
    items: [
      ['getting-started', 'Installation'],
      ['catalog-workflow', 'Your first catalog'],
      ['exports', 'Confluence and exports'],
    ],
  },
  {
    label: 'Link correctness',
    items: [
      ['sharepoint-mapping', 'Library mappings'],
      ['onedrive-diagnostics', 'OneDrive detection'],
      ['troubleshooting', 'Troubleshooting'],
      ['privacy', 'Privacy and limits'],
    ],
  },
  {
    label: 'Build and contribute',
    items: [
      ['architecture', 'Architecture'],
      ['build', 'Windows packaging'],
      ['validation', 'Release validation'],
      ['website', 'Documentation site'],
    ],
  },
];
export const docs = navigation.flatMap(group => group.items);
