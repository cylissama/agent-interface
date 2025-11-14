const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const listDocuments = async () => {
  const response = await fetch(`${API_BASE_URL}/documents/`);
  if (!response.ok) {
    throw new Error("Failed to fetch documents");
  }
  return response.json();
};

export const sendMessage = async ({ conversationId, content }) => {
  const response = await fetch(`${API_BASE_URL}/chat/completion`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ conversation_id: conversationId, role: "user", content })
  });

  if (!response.ok) {
    throw new Error("Failed to send message");
  }

  return response.json();
};
