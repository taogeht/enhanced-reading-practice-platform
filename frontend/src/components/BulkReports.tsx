// Bulk Report Generation component - Phase 3

import React, { useState, useEffect } from 'react';
import { ClassListItem } from '../types';
import { analyticsAPI } from '../services/api';

interface ReportOption {
  type: string;
  title: string;
  description: string;
  endpoint: string;
  class_id?: number;
}

interface BulkReportsProps {
  classes: ClassListItem[];
}

export const BulkReports: React.FC<BulkReportsProps> = ({ classes }) => {
  const [availableReports, setAvailableReports] = useState<ReportOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [generatingReports, setGeneratingReports] = useState<Set<string>>(new Set());
  const [selectedFormat, setSelectedFormat] = useState<'csv' | 'json'>('csv');

  useEffect(() => {
    loadAvailableReports();
  }, []);

  const loadAvailableReports = async () => {
    try {
      setLoading(true);
      const response = await analyticsAPI.getAvailableReports();
      setAvailableReports(response.available_reports || []);
    } catch (err: any) {
      setError('Failed to load available reports.');
      console.error('Reports load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async (report: ReportOption) => {
    const reportKey = `${report.type}_${report.class_id || 'general'}`;
    
    try {
      setGeneratingReports(prev => new Set([...prev, reportKey]));
      setError('');

      // Create download URL with format parameter
      const url = `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api${report.endpoint}?format=${selectedFormat}`;
      
      // Create a temporary anchor element to trigger download
      const link = document.createElement('a');
      link.href = url;
      link.download = `${report.type}_${new Date().toISOString().split('T')[0]}.${selectedFormat}`;
      
      // Add authorization header by fetching and creating blob URL
      const token = localStorage.getItem('token');
      const response = await fetch(url, {
        headers: {
          'Authorization': `Token ${token}`,
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to generate report: ${response.statusText}`);
      }

      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      
      link.href = blobUrl;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Clean up blob URL
      window.URL.revokeObjectURL(blobUrl);

    } catch (err: any) {
      setError(`Failed to generate ${report.title}. Please try again.`);
      console.error('Report generation error:', err);
    } finally {
      setGeneratingReports(prev => {
        const newSet = new Set(prev);
        newSet.delete(reportKey);
        return newSet;
      });
    }
  };

  const getReportIcon = (reportType: string) => {
    switch (reportType) {
      case 'teacher_summary': return '👨‍🏫';
      case 'class_performance': return '📊';
      case 'gradebook_export': return '📚';
      case 'student_progress': return '📈';
      case 'school_wide': return '🏫';
      default: return '📄';
    }
  };

  const getReportColor = (reportType: string) => {
    switch (reportType) {
      case 'teacher_summary': return '#1976d2';
      case 'class_performance': return '#388e3c';
      case 'gradebook_export': return '#f57c00';
      case 'student_progress': return '#7b1fa2';
      case 'school_wide': return '#d32f2f';
      default: return '#757575';
    }
  };

  if (loading) {
    return <div className="loading">Loading report options...</div>;
  }

  return (
    <div className="bulk-reports">
      <div className="section-header">
        <h2>Bulk Report Generation</h2>
        <p>Generate comprehensive reports for analysis and record-keeping.</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="format-selector">
        <h3>Export Format</h3>
        <div className="format-options">
          <label className={`format-option ${selectedFormat === 'csv' ? 'selected' : ''}`}>
            <input
              type="radio"
              value="csv"
              checked={selectedFormat === 'csv'}
              onChange={(e) => setSelectedFormat(e.target.value as 'csv')}
            />
            <span className="format-icon">📊</span>
            <div className="format-info">
              <strong>CSV</strong>
              <p>Spreadsheet-compatible format for analysis</p>
            </div>
          </label>

          <label className={`format-option ${selectedFormat === 'json' ? 'selected' : ''}`}>
            <input
              type="radio"
              value="json"
              checked={selectedFormat === 'json'}
              onChange={(e) => setSelectedFormat(e.target.value as 'json')}
            />
            <span className="format-icon">📋</span>
            <div className="format-info">
              <strong>JSON</strong>
              <p>Structured data format for integration</p>
            </div>
          </label>
        </div>
      </div>

      <div className="reports-section">
        <h3>Available Reports</h3>
        
        {availableReports.length === 0 ? (
          <div className="empty-state">
            <p>No reports available. Create some classes and assignments to generate reports.</p>
          </div>
        ) : (
          <div className="reports-grid">
            {availableReports.map((report) => {
              const reportKey = `${report.type}_${report.class_id || 'general'}`;
              const isGenerating = generatingReports.has(reportKey);
              
              return (
                <div 
                  key={reportKey} 
                  className="report-card"
                  style={{borderLeft: `4px solid ${getReportColor(report.type)}`}}
                >
                  <div className="report-header">
                    <span className="report-icon">{getReportIcon(report.type)}</span>
                    <h4>{report.title}</h4>
                  </div>
                  
                  <div className="report-content">
                    <p>{report.description}</p>
                  </div>
                  
                  <div className="report-actions">
                    <button
                      onClick={() => generateReport(report)}
                      disabled={isGenerating}
                      className="generate-button"
                      style={{backgroundColor: getReportColor(report.type)}}
                    >
                      {isGenerating ? (
                        <>⏳ Generating...</>
                      ) : (
                        <>⬇️ Download {selectedFormat.toUpperCase()}</>
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="bulk-actions">
        <h3>Bulk Operations</h3>
        <div className="bulk-options">
          <button
            onClick={() => {
              availableReports.forEach(report => {
                setTimeout(() => generateReport(report), Math.random() * 2000);
              });
            }}
            disabled={availableReports.length === 0 || generatingReports.size > 0}
            className="bulk-download-button"
          >
            📦 Download All Reports
          </button>
          
          <div className="bulk-info">
            <p>
              Generate all available reports at once. Files will be downloaded automatically 
              with timestamps and proper naming conventions.
            </p>
          </div>
        </div>
      </div>

      <div className="reports-info">
        <h3>📋 Report Types</h3>
        <div className="info-grid">
          <div className="info-card">
            <h4>👨‍🏫 Teacher Summary</h4>
            <p>Overview of all your classes, student counts, and performance metrics.</p>
            <ul>
              <li>Class performance averages</li>
              <li>Student engagement metrics</li>
              <li>Flag summary and trends</li>
            </ul>
          </div>
          
          <div className="info-card">
            <h4>📊 Class Performance</h4>
            <p>Detailed analytics for individual classes with student-level data.</p>
            <ul>
              <li>Individual student performance</li>
              <li>Completion and submission rates</li>
              <li>Progress trends and insights</li>
            </ul>
          </div>
          
          <div className="info-card">
            <h4>📚 Gradebook Export</h4>
            <p>LMS-compatible gradebook format for seamless integration.</p>
            <ul>
              <li>Numeric grades for assignments</li>
              <li>Fluency and accuracy scores</li>
              <li>Submission timestamps</li>
            </ul>
          </div>
          
          <div className="info-card">
            <h4>📈 Student Progress</h4>
            <p>Individual student journey with detailed timeline and improvements.</p>
            <ul>
              <li>Assignment completion history</li>
              <li>Score progression over time</li>
              <li>Teacher feedback records</li>
            </ul>
          </div>
        </div>
      </div>

      <div className="usage-tips">
        <h3>💡 Usage Tips</h3>
        <ul>
          <li><strong>CSV Format:</strong> Best for Excel, Google Sheets, or statistical analysis</li>
          <li><strong>JSON Format:</strong> Ideal for custom integrations or data processing</li>
          <li><strong>Regular Downloads:</strong> Generate reports weekly for progress tracking</li>
          <li><strong>Data Privacy:</strong> All reports respect class and student permissions</li>
          <li><strong>File Naming:</strong> Reports include dates for easy organization</li>
        </ul>
      </div>
    </div>
  );
};