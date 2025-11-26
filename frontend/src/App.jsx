import { useState } from "react";

import ChatInterface from "./components/ChatInterface.jsx";
import { sendMessage } from "./services/api.js";
import "./App.css";

const App = () => {
  const handleSend = async (message) => {
    try {
      const response = await sendMessage({ 
        conversationId: 1, 
        content: message.content,
        documentIds: message.documentIds || [],
        urls: message.urls || []
      });
      return response;
    } catch (error) {
      console.error("Failed to send message", error);
      return null;
    }
  };

  return (
    <div className="app-container">
      <div className="terminal-header">
        <pre className="terminal-title">{`   ___________ __ __  ___________
  / ____/ ___// // / / ____/ ___/
 / /    \\__ \\/ // /_/___ \\/ __ \\ 
/ /___ ___/ /__  __/___/ / /_/ / 
\\____//____/  /_/ /_____/\\____/  `}</pre>
      </div>
      <div className="chat-container">
        <ChatInterface onSend={handleSend} />
      </div>
    </div>
  );
};

export default App;
