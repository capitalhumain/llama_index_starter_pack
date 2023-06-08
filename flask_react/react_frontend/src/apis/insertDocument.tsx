const insertDocument = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('filename_as_doc_id', 'true');

  const response = await fetch('https://capitalhumain-bookish-space-couscous-p7xxj7vv4f75xj-5601.preview.app.github.dev/uploadFile', {
    mode: 'cors',
    method: 'POST',
    body: formData,
  });

  const responseText = response.text();
  return responseText;
};

export default insertDocument;
