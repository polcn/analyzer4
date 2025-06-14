import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import './FileUpload.css';

const FileUpload = ({ onUpload, loading, error }) => {
  const [fileType, setFileType] = useState('SM20');

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      onUpload(acceptedFiles[0], fileType);
    }
  }, [onUpload, fileType]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    disabled: loading,
    multiple: false
  });

  return (
    <div className="upload-container">
      <div className="file-type-selector">
        <label>File Type:</label>
        <select value={fileType} onChange={(e) => setFileType(e.target.value)} disabled={loading}>
          <option value="SM20">SM20 - Security Audit Log</option>
          <option value="CDHDR">CDHDR - Change Documents Header</option>
          <option value="CDPOS">CDPOS - Change Documents Items</option>
        </select>
      </div>

      <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''} ${loading ? 'disabled' : ''}`}>
        <input {...getInputProps()} />
        {loading ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>Analyzing file...</p>
          </div>
        ) : isDragActive ? (
          <p>Drop the file here...</p>
        ) : (
          <div>
            <p>Drag and drop a SAP export file here</p>
            <p className="alternative">or click to select a file</p>
            <p className="formats">Supported formats: CSV, XLS, XLSX</p>
          </div>
        )}
      </div>

      {error && (
        <div className="error-message">
          Error: {error}
        </div>
      )}
    </div>
  );
};

export default FileUpload;