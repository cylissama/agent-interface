import { useState } from "react";

const ChatInterface = ({ onSend }) => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!input.trim()) return;

    const userMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    if (onSend) {
      const response = await onSend(userMessage);
      if (response) {
        setMessages((prev) => [...prev, response]);
      }
    }
  };

  return (
    <div>
      <div>
        {messages.map((message, index) => (
          <div key={index}>
            <strong>{message.role}:</strong> {message.content}
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit}>
        <input value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ask a question" />
        <button type="submit">Send</button>
      </form>
    </div>
  );
};

export default ChatInterface;
