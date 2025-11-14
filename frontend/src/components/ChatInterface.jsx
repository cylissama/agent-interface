import { useState, useRef, useEffect } from "react";

const ChatInterface = ({ onSend }) => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [personality, setPersonality] = useState("");
  const [isLoadingPersonality, setIsLoadingPersonality] = useState(false);
  const [systemInfo, setSystemInfo] = useState(null);
  const [characterImage, setCharacterImage] = useState(null);
  const [cursorPosition, setCursorPosition] = useState({ top: 0, left: 0, visible: false });
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const cursorRef = useRef(null);
  const inputWrapperRef = useRef(null);

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
        const response = await fetch("http://localhost:8000/system/info");
        if (response.ok) {
          const info = await response.json();
          setSystemInfo(info);
          // Show system info message (only if no messages exist)
          if (messages.length === 0) {
            const systemMsg = {
              role: "system",
              content: `System detected: ${info.device}. Using model: ${info.recommended_model}`,
            };
            setMessages([systemMsg]);
          }
        }
      } catch (error) {
        console.error("Failed to get system info:", error);
      }
    };
    
    const loadConversation = async () => {
      try {
        const response = await fetch("http://localhost:8000/chat/conversation/1");
        if (response.ok) {
          const conversation = await response.json();
          if (conversation.character_image_url) {
            setCharacterImage(conversation.character_image_url);
          }
        }
      } catch (error) {
        // Conversation might not exist yet, that's okay
        console.error("Failed to load conversation:", error);
      }
    };
    
    checkSystemInfo();
    loadConversation();
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    if (onSend) {
      try {
        const response = await onSend(userMessage);
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
      const response = await fetch("http://localhost:8000/personality/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          character: personality.trim(),
          conversation_id: 1 
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      // Personality is now set on the backend for this conversation
      // Show confirmation message in the chat
      const confirmationMessage = {
        role: "system",
        content: `Personality set to: ${personality}`,
      };
      setMessages((prev) => [...prev, confirmationMessage]);
      
      // Store character image if provided
      if (data.character_image) {
        setCharacterImage(data.character_image);
      }
      
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

  useEffect(() => {
    adjustTextareaHeight();
    updateCursorPosition();
  }, [input]);

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
          </form>
        </div>
      </div>
      <div className="personality-container">
        <div className="personality-section">
          <label className="personality-label">Character Personality:</label>
          <input
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
          <button
            className="personality-button"
            onClick={handlePersonalityChange}
            disabled={!personality.trim() || isLoadingPersonality}
          >
            {isLoadingPersonality ? "Loading..." : "Set"}
          </button>
          <div className="character-profile">
            {characterImage ? (
              <div className="character-image">
                {characterImage.startsWith("data:image") ? (
                  <img 
                    src={characterImage} 
                    alt="Character" 
                    className="character-image-img"
                  />
                ) : (
                  <div className="image-placeholder">
                    {characterImage.substring(0, 100)}...
                  </div>
                )}
              </div>
            ) : (
              <div className="character-image-default">
                <span className="default-dash">—</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default ChatInterface;
