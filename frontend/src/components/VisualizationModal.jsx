import { useState, useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const VisualizationModal = ({ isOpen, onClose }) => {
  const [stats, setStats] = useState(null);
  const [sourceStats, setSourceStats] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      fetchStats();
    }
  }, [isOpen]);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/vectors/stats`);
      if (!response.ok) throw new Error("Failed to fetch stats");
      const data = await response.json();
      setStats(data);
      
      // Use real source_details from backend
      if (data.source_details && data.source_details.length > 0) {
        const sourceData = data.source_details.map((source) => ({
          name: source.name.length > 25 ? source.name.substring(0, 25) + "..." : source.name,
          fullName: source.name,
          chunks: source.chunks,
        }));
        setSourceStats(sourceData);
      } else {
        setSourceStats([]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const maxChunks = Math.max(...sourceStats.map(s => s.chunks), 1);

  return (
    <div className="viz-modal-overlay" onClick={onClose}>
      <div className="viz-modal" onClick={(e) => e.stopPropagation()}>
        <div className="viz-header">
          <span className="viz-title">[ VECTOR STORE ANALYTICS ]</span>
          <button className="viz-close" onClick={onClose}>×</button>
        </div>
        
        <div className="viz-content">
          {loading && (
            <div className="viz-loading">
              <span>Loading stats...</span>
              <div className="loading-bar"></div>
            </div>
          )}
          
          {error && (
            <div className="viz-error">
              <span>[ERROR] {error}</span>
              <button onClick={fetchStats} className="viz-retry">RETRY</button>
            </div>
          )}
          
          {!loading && !error && stats && (
            <>
              <div className="viz-stats-summary">
                <div className="stat-box">
                  <span className="stat-value">{stats.total_chunks || 0}</span>
                  <span className="stat-label">Total Chunks</span>
                </div>
                <div className="stat-box">
                  <span className="stat-value">{stats.unique_sources || 0}</span>
                  <span className="stat-label">Sources</span>
                </div>
                <div className="stat-box">
                  <span className="stat-value">{stats.embedding_model || "N/A"}</span>
                  <span className="stat-label">Model</span>
                </div>
              </div>
              
              <div className="viz-chart-section">
                <div className="chart-title">[ Chunks by Source ]</div>
                {sourceStats.length === 0 ? (
                  <div className="viz-empty">
                    <span>No indexed sources yet.</span>
                    <span className="viz-hint">Index documents or URLs to see analytics.</span>
                  </div>
                ) : (
                  <div className="bar-chart">
                    {sourceStats.map((source, idx) => (
                      <div key={idx} className="bar-row">
                        <span className="bar-label" title={source.fullName}>
                          {source.name}
                        </span>
                        <div className="bar-container">
                          <div 
                            className="bar-fill"
                            style={{ 
                              width: `${(source.chunks / maxChunks) * 100}%`,
                              backgroundColor: "#00ff00"
                            }}
                          />
                          <span className="bar-value">{source.chunks}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              <div className="viz-info">
                <span className="viz-hint">
                  Data retrieved from ChromaDB vector store
                </span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default VisualizationModal;
