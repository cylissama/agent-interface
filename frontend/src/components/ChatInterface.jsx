import { useState, useRef, useEffect } from "react";
import { getSystemInfo, generatePersonality } from "../services/api.js";

const ChatInterface = ({ onSend }) => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [personality, setPersonality] = useState("");
  const [isLoadingPersonality, setIsLoadingPersonality] = useState(false);
  const [systemInfo, setSystemInfo] = useState(null);
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [showSources, setShowSources] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const [urlCursorPosition, setUrlCursorPosition] = useState({ top: 0, left: 0, visible: false });
  const [cursorPosition, setCursorPosition] = useState({ top: 0, left: 0, visible: false });
  const [personalityCursorPosition, setPersonalityCursorPosition] = useState({ top: 0, left: 0, visible: false });
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const cursorRef = useRef(null);
  const inputWrapperRef = useRef(null);
  const personalityInputRef = useRef(null);
  const personalityCursorRef = useRef(null);
  const personalityWrapperRef = useRef(null);
  const fileInputRef = useRef(null);
  const hiddenFileInputRef = useRef(null);
  const urlInputRef = useRef(null);
  const urlCursorRef = useRef(null);
  const urlWrapperRef = useRef(null);

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

    // Merge URL context into the outgoing content if provided
    const trimmed = input.trim();
    const urlTrimmed = urlInput.trim();
    const combinedContent = urlTrimmed
      ? `${trimmed}\n\nSources:\n- ${urlTrimmed}`
      : trimmed;

    const userMessage = { role: "user", content: combinedContent };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    if (onSend) {
      try {
        const response = await onSend({
          ...userMessage,
          files: attachedFiles
        });
        if (response) {
          setMessages((prev) => [...prev, response]);
        }
      } catch (error) {
        console.error("Error sending message:", error);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "Sorry, I encountered an error. Please try again.",
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    }

    // Optional: reset sources after send
    setAttachedFiles([]);
    setUrlInput("");
    setShowSources(false);
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit(event);
    }
  };

  const handlePersonalityChange = async () => {
    if (!personality.trim() || isLoadingPersonality) return;
    
    setIsLoadingPersonality(true);
    try {
      const data = await generatePersonality({ 
        character: personality.trim(),
        conversationId: 1 
      });
      
      // Personality is now set on the backend for this conversation
      // Show confirmation message in the chat
      const confirmationMessage = {
        role: "system",
        content: `Personality set to: ${personality}`,
      };
      setMessages((prev) => [...prev, confirmationMessage]);
      
      setPersonality(""); // Clear the input field
    } catch (error) {
      console.error("Error setting personality:", error);
      const errorMessage = error.message || "Failed to set personality. Please try again.";
      // Show error message in the chat
      const errorMsg = {
        role: "system",
        content: `Error: ${errorMessage}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoadingPersonality(false);
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

  const updatePersonalityCursorPosition = () => {
    if (!personalityInputRef.current) return;

    const inputEl = personalityInputRef.current;
    const selectionStart = inputEl.selectionStart;
    const textBeforeCursor = personality.substring(0, selectionStart);

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

    const textNode = document.createTextNode(textBeforeCursor);
    mirror.appendChild(textNode);

    const cursorMarker = document.createElement('span');
    cursorMarker.style.display = 'inline-block';
    cursorMarker.style.width = '0';
    cursorMarker.style.height = '1em';
    mirror.appendChild(cursorMarker);

    document.body.appendChild(mirror);

    const markerRect = cursorMarker.getBoundingClientRect();
    const mirrorRect = mirror.getBoundingClientRect();

    document.body.removeChild(mirror);

    setPersonalityCursorPosition({
      top: Math.max(0, markerRect.top - mirrorRect.top),
      left: Math.max(0, markerRect.left - mirrorRect.left),
      visible: document.activeElement === inputEl
    });
  };

  useEffect(() => {
    adjustTextareaHeight();
    updateCursorPosition();
  }, [input]);

  useEffect(() => {
    updatePersonalityCursorPosition();
  }, [personality]);

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

    setUrlCursorPosition({
      top: Math.max(0, markerRect.top - mirrorRect.top),
      left: Math.max(0, markerRect.left - mirrorRect.left),
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

  useEffect(() => {
    const inputEl = personalityInputRef.current;
    if (!inputEl) return;

    const handleInput = () => {
      requestAnimationFrame(() => {
        setTimeout(updatePersonalityCursorPosition, 0);
      });
    };
    const handleClick = () => {
      requestAnimationFrame(() => {
        setTimeout(updatePersonalityCursorPosition, 0);
      });
    };
    const handleKey = () => {
      requestAnimationFrame(() => {
        setTimeout(updatePersonalityCursorPosition, 0);
      });
    };
    const handleFocus = () => {
      setPersonalityCursorPosition(prev => ({ ...prev, visible: true }));
      updatePersonalityCursorPosition();
    };
    const handleBlur = () => {
      setPersonalityCursorPosition(prev => ({ ...prev, visible: false }));
    };

    inputEl.addEventListener('input', handleInput);
    inputEl.addEventListener('click', handleClick);
    inputEl.addEventListener('keydown', handleKey);
    inputEl.addEventListener('keyup', handleKey);
    inputEl.addEventListener('focus', handleFocus);
    inputEl.addEventListener('blur', handleBlur);

    // Initial position
    updatePersonalityCursorPosition();

    return () => {
      inputEl.removeEventListener('input', handleInput);
      inputEl.removeEventListener('click', handleClick);
      inputEl.removeEventListener('keydown', handleKey);
      inputEl.removeEventListener('keyup', handleKey);
      inputEl.removeEventListener('focus', handleFocus);
      inputEl.removeEventListener('blur', handleBlur);
    };
  }, [personality]);

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
        <div className="sources-panel" style={{ marginTop: 8, marginBottom: 8, borderTop: "1px solid #2a2a2a", borderBottom: "1px solid #2a2a2a", padding: 8 }}>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-start" }}>
            {/* File input */}
            <div>
              <label style={{ display: "block", marginBottom: 4 }}>Attach files</label>
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
                  <button
                    type="button"
                    onClick={() => setAttachedFiles([])}
                    style={{ marginLeft: 8, fontSize: 12 }}
                  >
                    Clear
                  </button>
                </div>
              )}
            </div>
            {/* URLs input removed */}
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
                aria-label="Add files or URLs"
                title="Add files or URLs"
                onClick={() => {
                  // Open native file picker and reveal sources panel
                  setShowSources(true);
                  hiddenFileInputRef.current?.click();
                }}
                disabled={isLoading}
                style={{ display: "inline-flex", alignItems: "center", justifyContent: "center" }}
              >
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
            style={{ display: "none" }}
            onChange={(e) => {
              const files = Array.from(e.target.files ?? []);
              if (files.length) {
                setAttachedFiles(files);
                setShowSources(true);
              }
            }}
          />

        </div>
      </div>

      {/* Website URL box removed as requested */}
      <div className="personality-container">
        <div className="personality-section">
          <label className="personality-label">Character Personality:</label>
          <div className="textarea-wrapper" ref={personalityWrapperRef}>
            <input
              ref={personalityInputRef}
              type="text"
              className="personality-input"
              value={personality}
              onChange={(e) => setPersonality(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && personality.trim()) {
                  handlePersonalityChange();
                }
              }}
              placeholder="Enter character name (e.g., 'Trevor from GTA V')"
              disabled={isLoadingPersonality}
            />
            {personalityCursorPosition.visible && (
              <span
                ref={personalityCursorRef}
                className="terminal-cursor"
                style={{
                  top: `${personalityCursorPosition.top}px`,
                  left: `${personalityCursorPosition.left}px`,
                }}
              />
            )}
          </div>
          <button
            className="personality-button"
            onClick={handlePersonalityChange}
            disabled={!personality.trim() || isLoadingPersonality}
          >
            {isLoadingPersonality ? "Loading..." : "Set"}
          </button>
          {/* Profile picture display removed */}
        </div>
      </div>
      {/* Footer spacing not needed anymore */}
    </>
  );
};

export default ChatInterface;
