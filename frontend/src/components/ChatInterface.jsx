import { useState, useRef, useEffect } from "react";
import { getSystemInfo } from "../services/api.js";

const ChatInterface = ({ onSend }) => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [systemInfo, setSystemInfo] = useState(null);
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [showSources, setShowSources] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const [urls, setUrls] = useState([]);
  const [urlCursorPosition, setUrlCursorPosition] = useState({ top: 0, left: 0, visible: false });
  const [cursorPosition, setCursorPosition] = useState({ top: 0, left: 0, visible: false });
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const cursorRef = useRef(null);
  const inputWrapperRef = useRef(null);
  const fileInputRef = useRef(null);
  const hiddenFileInputRef = useRef(null);
  const urlInputRef = useRef(null);
  const urlCursorRef = useRef(null);
  const urlWrapperRef = useRef(null);

  // Estimate tokens using word count (more accurate: 1 token ≈ 0.75 words, or use word count directly)
  const estimateTokens = (text) => {
    // Use word count as approximation for tokens
    const words = text.split(/\s+/).filter(word => word.length > 0);
    return words.length;
  };

  // Calculate total context tokens
  const calculateContextTokens = () => {
    let total = 0;
    // Estimate tokens for files (we don't have content yet, so estimate based on file size)
    attachedFiles.forEach(file => {
      // Rough estimate: assume 50% of file size is text content
      // Estimate ~5 characters per word, so words ≈ (file.size * 0.5) / 5
      const estimatedWords = Math.floor((file.size * 0.5) / 5);
      total += estimatedWords; // Use word count as token approximation
    });
    // URLs will be processed server-side, so we can't estimate accurately
    // But we can show a note that they'll be included
    return total;
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Check system info and load conversation on mount
  useEffect(() => {
    const checkSystemInfo = async () => {
      try {
        const info = await getSystemInfo();
        setSystemInfo(info);
        // Show system info message (only if no messages exist)
        if (messages.length === 0) {
          const systemMsg = {
            role: "system",
            content: `System detected: ${info.device}. Using model: ${info.recommended_model}`,
          };
          setMessages([systemMsg]);
        }
      } catch (error) {
        console.error("Failed to get system info:", error);
      }
    };
    
    checkSystemInfo();
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!input.trim() || isLoading) return;

    const currentInput = input.trim();
    const userMessage = { role: "user", content: currentInput };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // Upload files if any
      let documentIds = [];
      if (attachedFiles.length > 0) {
        const { uploadDocuments } = await import("../services/api.js");
        const uploadedDocs = await uploadDocuments(Array.from(attachedFiles));
        documentIds = uploadedDocs.map(doc => doc.id);
      }
      
      // Process URLs if any
      let processedUrls = [];
      if (urls.length > 0) {
        console.log("URLs to send:", urls);
        const { processUrls } = await import("../services/api.js");
        await processUrls(urls);  // Process URLs to cache them
        processedUrls = urls;
      }
      
      console.log("Sending message with:", { documentIds, urls: processedUrls, content: currentInput });
      
      // Send message with context
      if (onSend) {
        const response = await onSend({
          ...userMessage,
          content: currentInput,
          documentIds,
          urls: processedUrls
        });
        if (response) {
          setMessages((prev) => [...prev, response]);
        }
      }
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${error.message || "Failed to process request"}`,
        },
      ]);
    } finally {
      setIsLoading(false);
      // Reset sources after send
      setAttachedFiles([]);
      setUrls([]);
      setUrlInput("");
      setShowSources(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit(event);
    }
  };


  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  };

  const updateCursorPosition = () => {
    if (!textareaRef.current) return;

    const textarea = textareaRef.current;
    const selectionStart = textarea.selectionStart;
    const textBeforeCursor = input.substring(0, selectionStart);
    
    // Create a mirror div with exact same styling as textarea
    const mirror = document.createElement('div');
    const textareaStyle = window.getComputedStyle(textarea);
    
    // Copy all textarea styles to mirror
    const stylesToCopy = [
      'font', 'fontSize', 'fontFamily', 'fontWeight', 'fontStyle',
      'letterSpacing', 'wordSpacing', 'textTransform', 'textIndent',
      'whiteSpace', 'wordWrap', 'wordBreak', 'lineHeight',
      'padding', 'border', 'boxSizing', 'width', 'margin'
    ];
    
    stylesToCopy.forEach(prop => {
      mirror.style[prop] = textareaStyle[prop];
    });
    
    // Ensure exact width match
    mirror.style.width = `${textarea.offsetWidth}px`;
    
    mirror.style.position = 'absolute';
    mirror.style.visibility = 'hidden';
    mirror.style.top = '-9999px';
    mirror.style.left = '-9999px';
    mirror.style.whiteSpace = 'pre-wrap';
    mirror.style.wordWrap = 'break-word';
    
    // Create text node for text before cursor
    const textNode = document.createTextNode(textBeforeCursor);
    mirror.appendChild(textNode);
    
    // Add a zero-width span to mark cursor position
    const cursorMarker = document.createElement('span');
    cursorMarker.style.display = 'inline-block';
    cursorMarker.style.width = '0';
    cursorMarker.style.height = '1em';
    mirror.appendChild(cursorMarker);
    
    // Append to body to measure
    document.body.appendChild(mirror);
    
    // Get the marker position
    const markerRect = cursorMarker.getBoundingClientRect();
    const mirrorRect = mirror.getBoundingClientRect();
    const textareaRect = textarea.getBoundingClientRect();
    
    // Calculate position relative to textarea
    // The cursor is positioned absolutely within textarea-wrapper, which contains the textarea
    const left = markerRect.left - mirrorRect.left;
    const top = markerRect.top - mirrorRect.top;
    
    // Clean up
    document.body.removeChild(mirror);
    
    setCursorPosition({
      top: Math.max(0, top),
      left: Math.max(0, left),
      visible: document.activeElement === textarea
    });
  };

  useEffect(() => {
    adjustTextareaHeight();
    updateCursorPosition();
  }, [input]);

  const updateUrlCursorPosition = () => {
    if (!urlInputRef.current) return;

    const inputEl = urlInputRef.current;
    const selectionStart = inputEl.selectionStart ?? 0;
    const textBeforeCursor = urlInput.substring(0, selectionStart);

    const mirror = document.createElement('div');
    const inputStyle = window.getComputedStyle(inputEl);
    const stylesToCopy = [
      'font', 'fontSize', 'fontFamily', 'fontWeight', 'fontStyle',
      'letterSpacing', 'wordSpacing', 'textTransform', 'textIndent',
      'whiteSpace', 'wordWrap', 'wordBreak', 'lineHeight',
      'padding', 'border', 'boxSizing', 'width', 'margin'
    ];
    stylesToCopy.forEach(prop => {
      mirror.style[prop] = inputStyle[prop];
    });
    mirror.style.width = `${inputEl.offsetWidth}px`;
    mirror.style.position = 'absolute';
    mirror.style.visibility = 'hidden';
    mirror.style.top = '-9999px';
    mirror.style.left = '-9999px';
    mirror.style.whiteSpace = 'pre-wrap';
    mirror.style.wordWrap = 'break-word';

    mirror.appendChild(document.createTextNode(textBeforeCursor));
    const cursorMarker = document.createElement('span');
    cursorMarker.style.display = 'inline-block';
    cursorMarker.style.width = '0';
    cursorMarker.style.height = '1em';
    mirror.appendChild(cursorMarker);

    document.body.appendChild(mirror);
    const markerRect = cursorMarker.getBoundingClientRect();
    const mirrorRect = mirror.getBoundingClientRect();
    document.body.removeChild(mirror);

    // Get the padding-left to ensure cursor starts at text position
    const paddingLeft = parseFloat(inputStyle.paddingLeft) || 8;
    const borderLeft = parseFloat(inputStyle.borderLeftWidth) || 2;
    const calculatedLeft = markerRect.left - mirrorRect.left;
    
    setUrlCursorPosition({
      top: Math.max(0, markerRect.top - mirrorRect.top),
      left: Math.max(paddingLeft + borderLeft, calculatedLeft),
      visible: document.activeElement === inputEl
    });
  };

  useEffect(() => {
    updateUrlCursorPosition();
  }, [urlInput]);

  useEffect(() => {
    const inputEl = urlInputRef.current;
    if (!inputEl) return;

    const handleInput = () => {
      requestAnimationFrame(() => {
        setTimeout(updateUrlCursorPosition, 0);
      });
    };
    const handleClick = handleInput;
    const handleKey = handleInput;
    const handleFocus = () => {
      setUrlCursorPosition(prev => ({ ...prev, visible: true }));
      updateUrlCursorPosition();
    };
    const handleBlur = () => {
      setUrlCursorPosition(prev => ({ ...prev, visible: false }));
    };

    inputEl.addEventListener('input', handleInput);
    inputEl.addEventListener('click', handleClick);
    inputEl.addEventListener('keydown', handleKey);
    inputEl.addEventListener('keyup', handleKey);
    inputEl.addEventListener('focus', handleFocus);
    inputEl.addEventListener('blur', handleBlur);

    updateUrlCursorPosition();

    return () => {
      inputEl.removeEventListener('input', handleInput);
      inputEl.removeEventListener('click', handleClick);
      inputEl.removeEventListener('keydown', handleKey);
      inputEl.removeEventListener('keyup', handleKey);
      inputEl.removeEventListener('focus', handleFocus);
      inputEl.removeEventListener('blur', handleBlur);
    };
  }, [urlInput]);
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    const handleInput = () => {
      requestAnimationFrame(() => {
        setTimeout(updateCursorPosition, 0);
      });
    };

    const handleClick = () => {
      requestAnimationFrame(() => {
        setTimeout(updateCursorPosition, 0);
      });
    };

    const handleKeyDown = () => {
      requestAnimationFrame(() => {
        setTimeout(updateCursorPosition, 0);
      });
    };

    const handleFocus = () => {
      setCursorPosition(prev => ({ ...prev, visible: true }));
      updateCursorPosition();
    };

    const handleBlur = () => {
      setCursorPosition(prev => ({ ...prev, visible: false }));
    };

    textarea.addEventListener('input', handleInput);
    textarea.addEventListener('click', handleClick);
    textarea.addEventListener('keydown', handleKeyDown);
    textarea.addEventListener('keyup', handleKeyDown);
    textarea.addEventListener('focus', handleFocus);
    textarea.addEventListener('blur', handleBlur);

    // Initial position
    updateCursorPosition();

    return () => {
      textarea.removeEventListener('input', handleInput);
      textarea.removeEventListener('click', handleClick);
      textarea.removeEventListener('keydown', handleKeyDown);
      textarea.removeEventListener('keyup', handleKeyDown);
      textarea.removeEventListener('focus', handleFocus);
      textarea.removeEventListener('blur', handleBlur);
    };
  }, [input]);

  return (
    <>
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="empty-state">
            <h2>How can I help you today?</h2>
            <p>Start a conversation by typing a message below.</p>
          </div>
        ) : (
          messages.map((message, index) => (
            <div key={index} className={`message message-${message.role} ${message.role === "system" ? "message-system" : ""}`}>
              <div className="message-avatar">
                {message.role === "user" ? "U" : message.role === "system" ? "*" : "AI"}
              </div>
              <div className="message-content">{message.content}</div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="message message-assistant">
            <div className="message-avatar">AI</div>
            <div className="message-content">
              <div className="loading-indicator">
                <div className="loading-dot"></div>
                <div className="loading-dot"></div>
                <div className="loading-dot"></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Sources panel ABOVE message box */}
      {showSources && (
        <div className="sources-panel" style={{ marginTop: 8, marginBottom: 8, borderTop: "1px solid #2a2a2a", borderBottom: "1px solid #2a2a2a", padding: 12, backgroundColor: "#1a1a1a", borderRadius: 4 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>Add Context Sources</h3>
                {(attachedFiles.length > 0 || urls.length > 0) && (
                  <div style={{ fontSize: 11, color: "#888" }}>
                    {attachedFiles.length} file(s), {urls.length} URL(s) • 
                    Estimated context: ~{calculateContextTokens().toLocaleString()} tokens
                    {urls.length > 0 && " (URLs will be processed server-side)"}
                  </div>
                )}
              </div>
              <button
                type="button"
                onClick={() => setShowSources(false)}
                style={{ background: "none", border: "none", color: "#888", cursor: "pointer", fontSize: 18, padding: 0, width: 24, height: 24 }}
                title="Close panel"
              >
                ×
              </button>
            </div>
            {/* File input */}
            <div>
              <label style={{ display: "block", marginBottom: 6, fontSize: 13 }}>Attach files (PDF, TXT, DOC, DOCX, MD, RTF, CSV)</label>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <button
                  type="button"
                  className="send-button"
                  onClick={() => hiddenFileInputRef.current?.click()}
                  title="Choose files"
                >
                  Choose files
                </button>
                {attachedFiles.length > 0 && (
                  <span style={{ fontSize: 12 }}>{attachedFiles.length} file(s) selected</span>
                )}
              </div>
              {attachedFiles.length > 0 && (
                <div style={{ marginTop: 4, fontSize: 12 }}>
                  {Array.from(attachedFiles).map((file, idx) => {
                    const fileSizeKB = (file.size / 1024).toFixed(1);
                    // Rough estimate: assume 50% of file size is text, ~5 chars per word
                    const estimatedTokens = Math.floor((file.size * 0.5) / 5);
                    return (
                      <div key={idx} style={{ 
                        marginBottom: 4, 
                        display: "flex", 
                        alignItems: "center", 
                        gap: 8,
                        padding: 6,
                        backgroundColor: "#0a0a0a",
                        borderRadius: 4
                      }}>
                        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 2 }}>
                          <span style={{ fontWeight: 500 }}>{file.name}</span>
                          <span style={{ fontSize: 11, color: "#888" }}>
                            {fileSizeKB} KB • ~{estimatedTokens.toLocaleString()} tokens
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            const newFiles = Array.from(attachedFiles).filter((_, i) => i !== idx);
                            setAttachedFiles(newFiles);
                          }}
                          style={{ fontSize: 11, padding: "4px 8px", background: "#ef4444", color: "white", border: "none", borderRadius: 3, cursor: "pointer" }}
                        >
                          Remove
                        </button>
                      </div>
                    );
                  })}
                  <button
                    type="button"
                    onClick={() => setAttachedFiles([])}
                    style={{ marginTop: 4, fontSize: 11, background: "none", border: "none", color: "#888", cursor: "pointer", textDecoration: "underline" }}
                  >
                    Clear all files
                  </button>
                </div>
              )}
            </div>
            
            {/* URL input */}
            <div>
              <label style={{ display: "block", marginBottom: 6, fontSize: 13 }}>Add website URLs</label>
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <input
                  type="text"
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && urlInput.trim()) {
                      e.preventDefault();
                      const trimmed = urlInput.trim();
                      // Basic URL validation
                      if (trimmed && !urls.includes(trimmed)) {
                        // Add http:// if no protocol is specified
                        const urlToAdd = trimmed.startsWith('http://') || trimmed.startsWith('https://') 
                          ? trimmed 
                          : `https://${trimmed}`;
                        setUrls([...urls, urlToAdd]);
                        setUrlInput("");
                      }
                    }
                  }}
                  placeholder="Enter URL (e.g., example.com) and press Enter"
                  style={{ flex: 1, padding: 6, background: "#0a0a0a", color: "#fff", border: "1px solid #2a2a2a", borderRadius: 4, fontSize: 13 }}
                />
                <button
                  type="button"
                  className="send-button"
                  onClick={() => {
                    if (urlInput.trim()) {
                      const trimmed = urlInput.trim();
                      if (trimmed && !urls.includes(trimmed)) {
                        const urlToAdd = trimmed.startsWith('http://') || trimmed.startsWith('https://') 
                          ? trimmed 
                          : `https://${trimmed}`;
                        setUrls([...urls, urlToAdd]);
                        setUrlInput("");
                      }
                    }
                  }}
                  disabled={!urlInput.trim()}
                  title="Add URL"
                >
                  Add
                </button>
              </div>
              {urls.length > 0 && (
                <div style={{ marginTop: 4, fontSize: 12 }}>
                  {urls.map((url, idx) => (
                    <div key={idx} style={{ 
                      marginBottom: 4, 
                      display: "flex", 
                      alignItems: "center", 
                      gap: 8,
                      padding: 6,
                      backgroundColor: "#0a0a0a",
                      borderRadius: 4
                    }}>
                      <div style={{ flex: 1 }}>
                        <span style={{ wordBreak: "break-all", display: "block" }}>{url}</span>
                        <span style={{ fontSize: 11, color: "#888" }}>
                          Will be processed when message is sent
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          setUrls(urls.filter((_, i) => i !== idx));
                        }}
                        style={{ fontSize: 11, padding: "4px 8px", background: "#ef4444", color: "white", border: "none", borderRadius: 3, cursor: "pointer" }}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => {
                      setUrls([]);
                      setUrlInput("");
                    }}
                    style={{ marginTop: 4, fontSize: 11, background: "none", border: "none", color: "#888", cursor: "pointer", textDecoration: "underline" }}
                  >
                    Clear all URLs
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      <div className="input-container">
        <div className="input-wrapper" ref={inputWrapperRef}>
          <form onSubmit={handleSubmit} className="input-form">
            <div className="textarea-wrapper">
              <textarea
                ref={textareaRef}
                className="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Message Agent Interface..."
                rows={1}
                disabled={isLoading}
                style={{ caretColor: cursorPosition.visible ? "transparent" : undefined }}
              />
              {cursorPosition.visible && (
                <span
                  ref={cursorRef}
                  className="terminal-cursor"
                  style={{
                    top: `${cursorPosition.top}px`,
                    left: `${cursorPosition.left}px`,
                  }}
                />
              )}
            </div>
            {/* Attachments button (left of Send) */}
            <div className="attachments-controls" style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <button
                type="button"
                className="send-button"
                aria-label="Attach files"
                title="Attach files"
                onClick={() => {
                  // Open file picker directly
                  hiddenFileInputRef.current?.click();
                }}
                disabled={isLoading}
                style={{ 
                  display: "inline-flex", 
                  alignItems: "center", 
                  justifyContent: "center",
                  position: "relative"
                }}
              >
                {(attachedFiles.length > 0 || urls.length > 0) && (
                  <span 
                    onClick={(e) => {
                      e.stopPropagation(); // Don't open file picker
                      setShowSources(!showSources); // Toggle sources panel to view/manage
                    }}
                    style={{
                      position: "absolute",
                      top: -6,
                      right: -6,
                      backgroundColor: "#00ff00",
                      color: "#000000",
                      border: "1px solid #000000",
                      width: 18,
                      height: 18,
                      fontSize: 10,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontWeight: "bold",
                      cursor: "pointer",
                      fontFamily: "'Courier New', Courier, monospace"
                    }}
                    title="Click to view/manage attached sources"
                  >
                    {attachedFiles.length + urls.length}
                  </span>
                )}
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M16.5 6.5l-7.78 7.78a3 3 0 104.24 4.24l7.07-7.07a5 5 0 10-7.07-7.07L6.4 8.85" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </button>
              <button
                type="submit"
                className="send-button"
                disabled={!input.trim() || isLoading}
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 16 16"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    d="M.5 1.163l1.5 1.5L8 8l-6 5.337-1.5 1.5L0 15.5V.5z"
                    fill="currentColor"
                  />
                </svg>
              </button>
            </div>
          </form>

          {/* Hidden file input to trigger system file picker from the attach button */}
          <input
            ref={hiddenFileInputRef}
            type="file"
            multiple
            accept=".pdf,.txt,.doc,.docx,.md,.rtf,.csv"
            style={{ display: "none" }}
            onChange={(e) => {
              const files = Array.from(e.target.files ?? []);
              if (files.length) {
                // Append new files to existing ones
                setAttachedFiles(prev => [...prev, ...files]);
                setShowSources(true); // Show panel so user can see attached files
              }
              // Reset the input so the same file can be selected again if needed
              e.target.value = '';
            }}
          />

        </div>
      </div>

      {/* Website URL context box */}
      <div className="personality-container" style={{ 
        position: 'absolute',
        top: 'calc(60vh + 80px)', /* Position below chat input */
        left: 0,
        right: 0,
        width: '100%'
      }}>
        <div className="personality-section">
          <label className="personality-label">Website URL Context:</label>
          <div style={{ display: "flex", gap: 8, alignItems: "center", width: "100%" }}>
            <div className="url-input-wrapper" ref={urlWrapperRef}>
              <input
                ref={urlInputRef}
                type="text"
                className="personality-input"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && urlInput.trim()) {
                    e.preventDefault();
                    const trimmed = urlInput.trim();
                    if (trimmed && !urls.includes(trimmed)) {
                      // Add http:// if no protocol is specified
                      const urlToAdd = trimmed.startsWith('http://') || trimmed.startsWith('https://') 
                        ? trimmed 
                        : `https://${trimmed}`;
                      setUrls([...urls, urlToAdd]);
                      setUrlInput("");
                    }
                  }
                }}
                placeholder="Enter website URL (e.g., example.com or https://example.com)"
              />
              {urlCursorPosition.visible && (
                <span
                  ref={urlCursorRef}
                  className="url-terminal-cursor"
                  style={{
                    left: `${urlCursorPosition.left}px`,
                  }}
                />
              )}
            </div>
            <button
              className="personality-button"
              onClick={() => {
                if (urlInput.trim()) {
                  const trimmed = urlInput.trim();
                  if (trimmed && !urls.includes(trimmed)) {
                    const urlToAdd = trimmed.startsWith('http://') || trimmed.startsWith('https://') 
                      ? trimmed 
                      : `https://${trimmed}`;
                    setUrls([...urls, urlToAdd]);
                    setUrlInput("");
                  }
                }
              }}
              disabled={!urlInput.trim()}
            >
              Add URL
            </button>
          </div>
          {urls.length > 0 && (
            <div style={{ marginTop: 8, fontSize: 12, fontFamily: "'Courier New', Courier, monospace" }}>
              <div style={{ marginBottom: 4, color: "#00cc00" }}>[ADDED URLs: {urls.length}]</div>
              {urls.map((url, idx) => (
                <div key={idx} style={{ 
                  marginBottom: 4, 
                  display: "flex", 
                  alignItems: "center", 
                  gap: 8,
                  padding: "4px 8px",
                  backgroundColor: "#000000",
                  border: "1px solid #004400",
                  borderLeft: "2px solid #00ff00"
                }}>
                  <span style={{ flex: 1, wordBreak: "break-all", fontSize: 12, color: "#00ff00" }}>{url}</span>
                  <button
                    type="button"
                    onClick={() => {
                      setUrls(urls.filter((_, i) => i !== idx));
                    }}
                    style={{ 
                      fontSize: 11, 
                      padding: "2px 8px",
                      background: "#000000",
                      color: "#00ff00",
                      border: "1px solid #00ff00",
                      cursor: "pointer",
                      fontFamily: "'Courier New', Courier, monospace"
                    }}
                    onMouseOver={(e) => { e.target.style.background = "#00ff00"; e.target.style.color = "#000000"; }}
                    onMouseOut={(e) => { e.target.style.background = "#000000"; e.target.style.color = "#00ff00"; }}
                  >
                    [X]
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={() => {
                  setUrls([]);
                  setUrlInput("");
                }}
                style={{ 
                  marginTop: 4, 
                  fontSize: 11,
                  background: "none",
                  border: "none",
                  color: "#00cc00",
                  cursor: "pointer",
                  fontFamily: "'Courier New', Courier, monospace"
                }}
                onMouseOver={(e) => { e.target.style.color = "#00ff00"; }}
                onMouseOut={(e) => { e.target.style.color = "#00cc00"; }}
              >
                [CLEAR ALL]
              </button>
            </div>
          )}
        </div>
      </div>
      {/* Footer spacing not needed anymore */}
    </>
  );
};

export default ChatInterface;
