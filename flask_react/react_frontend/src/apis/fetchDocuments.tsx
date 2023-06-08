export type Document = {
  id: string;
  text: string;
};

const fetchDocuments = async (): Promise<Document[]> => {
  const response = await fetch('https://capitalhumain-bookish-space-couscous-p7xxj7vv4f75xj-5601.preview.app.github.dev/getDocuments', { mode: 'cors' });

  if (!response.ok) {
    return [];
  }

  const documentList = (await response.json()) as Document[];
  return documentList;
};

export default fetchDocuments;
