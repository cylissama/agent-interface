import { useEffect, useState } from "react";

import AnswerDisplay from "./components/AnswerDisplay.jsx";
import ChatInterface from "./components/ChatInterface.jsx";
import DocumentList from "./components/DocumentList.jsx";
import FileUpload from "./components/FileUpload.jsx";
import { listDocuments, sendMessage } from "./services/api.js";

const App = () => {
  const [documents, setDocuments] = useState([]);
  const [lastAnswer, setLastAnswer] = useState("");

  useEffect(() => {
    listDocuments()
      .then(setDocuments)
      .catch((error) => {
        console.error("Failed to load documents", error);
      });
  }, []);

  const handleUpload = (file) => {
    console.log("Upload", file);
  };

  const handleSend = async (message) => {
    try {
      const response = await sendMessage({ conversationId: 1, content: message.content });
      setLastAnswer(response.content);
      return response;
    } catch (error) {
      console.error("Failed to send message", error);
      return null;
    }
  };

  return (
    <div>
      <h1>Agent Interface</h1>
      <FileUpload onUpload={handleUpload} />
      <DocumentList documents={documents} />
      <ChatInterface onSend={handleSend} />
      <AnswerDisplay answer={lastAnswer} />
    </div>
  );
};

export default App;
