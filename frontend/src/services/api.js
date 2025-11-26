const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const listDocuments = async () => {
  const response = await fetch(`${API_BASE_URL}/documents/`);
  if (!response.ok) {
    throw new Error("Failed to fetch documents");
  }
  return response.json();
};

export const uploadDocuments = async (files) => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });
  
  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    body: formData,
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || 'Failed to upload documents');
  }
  
  return response.json();
};

export const processUrls = async (urls) => {
  const response = await fetch(`${API_BASE_URL}/documents/urls`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(urls),
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || 'Failed to process URLs');
  }
  
  return response.json();
};

export const sendMessage = async ({ conversationId, content, documentIds = [], urls = [] }) => {
  console.log("sendMessage called with:", { conversationId, content, documentIds, urls });
  const params = new URLSearchParams();
  params.append('conversation_id', conversationId);
  
  if (documentIds.length > 0) {
    documentIds.forEach(id => params.append('document_ids', id));
  }
  
  if (urls.length > 0) {
    urls.forEach(url => params.append('urls', url));
  }
  
  const url = `${API_BASE_URL}/chat/completion?${params.toString()}`;
  console.log("Sending request to:", url);
  console.log("Query params:", params.toString());
  
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation_id: conversationId, role: 'user', content })
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || 'Failed to send message');
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