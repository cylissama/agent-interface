import { useState } from "react";

const FileUpload = ({ onUpload }) => {
  const [file, setFile] = useState(null);

  const handleSubmit = (event) => {
    event.preventDefault();
    if (file && onUpload) {
      onUpload(file);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input type="file" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
      <button type="submit">Upload</button>
    </form>
  );
};

export default FileUpload;
