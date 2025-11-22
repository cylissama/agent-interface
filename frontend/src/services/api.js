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

export const getSystemInfo = async () => {
  const response = await fetch(`${API_BASE_URL}/system/info`);
  if (!response.ok) {
    throw new Error("Failed to fetch system info");
  }
  return response.json();
};

export const generatePersonality = async ({ character, conversationId }) => {
  try {
    const response = await fetch(`${API_BASE_URL}/personality/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        character: character.trim(),
        conversation_id: conversationId 
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  } catch (error) {
    // Handle network errors (backend not running, CORS, etc.)
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(`Cannot connect to backend at ${API_BASE_URL}. Make sure the backend server is running.`);
    }
    throw error;
  }
};