const DocumentList = ({ documents }) => {
  if (!documents?.length) {
    return <p>No documents uploaded yet.</p>;
  }

  return (
    <ul>
      {documents.map((document) => (
        <li key={document.id}>{document.name}</li>
      ))}
    </ul>
  );
};

export default DocumentList;
