import React, { useState } from 'react';
import './App.css';
import FileUpload from './components/FileUpload';
import AnalysisResults from './components/AnalysisResults';
import { analyzeFile, getResults } from './services/api';

function App() {
  const [analysisId, setAnalysisId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleFileUpload = async (file, fileType) => {
    setLoading(true);
    setError(null);
    
    try {
      // Start analysis
      const { analysisId } = await analyzeFile(file, fileType);
      setAnalysisId(analysisId);
      
      // Poll for results
      const pollResults = async () => {
        const data = await getResults(analysisId);
        
        if (data.status === 'completed') {
          setResults(data);
          setLoading(false);
        } else if (data.status === 'failed') {
          setError(data.error || 'Analysis failed');
          setLoading(false);
        } else {
          // Continue polling
          setTimeout(pollResults, 2000);
        }
      };
      
      setTimeout(pollResults, 2000);
      
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>SAP Analyzer 4</h1>
        <p>Upload SAP export files for security analysis</p>
      </header>
      
      <main className="App-main">
        {!results && (
          <FileUpload 
            onUpload={handleFileUpload}
            loading={loading}
            error={error}
          />
        )}
        
        {results && (
          <AnalysisResults 
            results={results}
            onReset={() => {
              setResults(null);
              setAnalysisId(null);
            }}
          />
        )}
      </main>
    </div>
  );
}

export default App;