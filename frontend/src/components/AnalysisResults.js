import React from 'react';
import './AnalysisResults.css';

const AnalysisResults = ({ results, onReset }) => {
  const summary = results.summary || {};
  
  return (
    <div className="results-container">
      <div className="results-header">
        <h2>Analysis Complete</h2>
        <button onClick={onReset} className="new-analysis-btn">
          New Analysis
        </button>
      </div>

      <div className="results-summary">
        <div className="summary-card">
          <h3>Analysis Summary</h3>
          <div className="summary-stats">
            <div className="stat">
              <span className="stat-label">File Type:</span>
              <span className="stat-value">{results.fileType}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Total Records:</span>
              <span className="stat-value">{summary.total_records || 0}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Flagged Records:</span>
              <span className="stat-value flagged">{summary.flagged_records || 0}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Detection Rate:</span>
              <span className="stat-value">
                {summary.total_records > 0 
                  ? ((summary.flagged_records / summary.total_records) * 100).toFixed(2) 
                  : 0}%
              </span>
            </div>
          </div>
        </div>

        {summary.flag_counts && (
          <div className="summary-card">
            <h3>Detection Flags</h3>
            <div className="flag-counts">
              {Object.entries(summary.flag_counts).map(([flag, count]) => (
                <div key={flag} className="flag-item">
                  <span className="flag-name">{flag.replace(/_/g, ' ')}</span>
                  <span className="flag-count">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="download-section">
        {results.downloadUrl && (
          <a 
            href={results.downloadUrl} 
            className="download-btn"
            download
          >
            Download Analyzed CSV
          </a>
        )}
      </div>

      <div className="results-details">
        <h3>Analysis Details</h3>
        <div className="details-content">
          <p><strong>Analysis ID:</strong> {results.analysisId}</p>
          <p><strong>Completed:</strong> {new Date(results.timestamp).toLocaleString()}</p>
        </div>
      </div>
    </div>
  );
};

export default AnalysisResults;