// Bulk Audio Generation component for teachers - Phase 2

import React, { useState, useEffect } from 'react';
import { StoryListItem } from '../types';
import { storiesAPI } from '../services/api';

interface BulkGenerationJob {
  id: string;
  stories: StoryListItem[];
  voiceTypes: string[];
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  totalFiles: number;
  completedFiles: number;
  startedAt: string;
  estimatedCompletion?: string;
}

export const BulkAudioGeneration: React.FC = () => {
  const [stories, setStories] = useState<StoryListItem[]>([]);
  const [selectedStories, setSelectedStories] = useState<Set<number>>(new Set());
  const [selectedVoices, setSelectedVoices] = useState<Set<string>>(new Set(['female_1']));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [generationJobs, setGenerationJobs] = useState<BulkGenerationJob[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

  const availableVoices = [
    { id: 'female_1', name: 'Female Voice 1', description: 'Clear, professional female voice' },
    { id: 'female_2', name: 'Female Voice 2', description: 'Warm, storytelling female voice' },
    { id: 'male_1', name: 'Male Voice 1', description: 'Deep, authoritative male voice' },
    { id: 'male_2', name: 'Male Voice 2', description: 'Friendly, conversational male voice' },
  ];

  useEffect(() => {
    loadStories();
  }, []);

  const loadStories = async () => {
    try {
      setLoading(true);
      const response = await storiesAPI.getStories();
      setStories(response.results);
    } catch (err: any) {
      setError('Failed to load stories.');
    } finally {
      setLoading(false);
    }
  };

  const handleStorySelect = (storyId: number) => {
    const newSelected = new Set(selectedStories);
    if (newSelected.has(storyId)) {
      newSelected.delete(storyId);
    } else {
      newSelected.add(storyId);
    }
    setSelectedStories(newSelected);
  };

  const handleVoiceSelect = (voiceId: string) => {
    const newSelected = new Set(selectedVoices);
    if (newSelected.has(voiceId)) {
      newSelected.delete(voiceId);
    } else {
      newSelected.add(voiceId);
    }
    setSelectedVoices(newSelected);
  };

  const handleSelectAllStories = () => {
    if (selectedStories.size === stories.length) {
      setSelectedStories(new Set());
    } else {
      setSelectedStories(new Set(stories.map(s => s.id)));
    }
  };

  const handleSelectAllVoices = () => {
    if (selectedVoices.size === availableVoices.length) {
      setSelectedVoices(new Set());
    } else {
      setSelectedVoices(new Set(availableVoices.map(v => v.id)));
    }
  };

  const getSelectedStoriesData = () => {
    return stories.filter(story => selectedStories.has(story.id));
  };

  const calculateTotalFiles = () => {
    return selectedStories.size * selectedVoices.size;
  };

  const estimateGenerationTime = () => {
    const totalFiles = calculateTotalFiles();
    const estimatedSeconds = totalFiles * 30; // Assume 30 seconds per file
    const hours = Math.floor(estimatedSeconds / 3600);
    const minutes = Math.floor((estimatedSeconds % 3600) / 60);
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };

  const handleStartGeneration = async () => {
    if (selectedStories.size === 0 || selectedVoices.size === 0) {
      setError('Please select at least one story and one voice type.');
      return;
    }

    try {
      setIsGenerating(true);
      setError('');

      const newJob: BulkGenerationJob = {
        id: Date.now().toString(),
        stories: getSelectedStoriesData(),
        voiceTypes: Array.from(selectedVoices),
        status: 'pending',
        progress: 0,
        totalFiles: calculateTotalFiles(),
        completedFiles: 0,
        startedAt: new Date().toISOString(),
        estimatedCompletion: new Date(Date.now() + (calculateTotalFiles() * 30000)).toISOString()
      };

      setGenerationJobs(prev => [newJob, ...prev]);

      // Here you would normally call an API to start the bulk generation
      // For now, we'll simulate the process
      simulateGeneration(newJob.id);

      // Reset selections
      setSelectedStories(new Set());
      setSelectedVoices(new Set(['female_1']));

    } catch (err: any) {
      setError('Failed to start audio generation.');
    } finally {
      setIsGenerating(false);
    }
  };

  const simulateGeneration = (jobId: string) => {
    const updateProgress = () => {
      setGenerationJobs(prev => 
        prev.map(job => {
          if (job.id === jobId) {
            const newProgress = Math.min(job.progress + Math.random() * 15, 100);
            const completedFiles = Math.floor((newProgress / 100) * job.totalFiles);
            
            return {
              ...job,
              progress: newProgress,
              completedFiles,
              status: newProgress >= 100 ? 'completed' : 'processing'
            };
          }
          return job;
        })
      );
    };

    const interval = setInterval(() => {
      setGenerationJobs(prev => {
        const job = prev.find(j => j.id === jobId);
        if (!job || job.progress >= 100) {
          clearInterval(interval);
          return prev;
        }
        return prev;
      });
      
      updateProgress();
    }, 2000);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return '⏳';
      case 'processing': return '🔄';
      case 'completed': return '✅';
      case 'failed': return '❌';
      default: return '⏳';
    }
  };

  if (loading) {
    return <div className="loading">Loading stories...</div>;
  }

  return (
    <div className="bulk-audio-generation">
      <div className="section-header">
        <h2>Bulk Audio Generation</h2>
        <p>Generate TTS audio files in bulk for multiple stories and voice types.</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Story Selection */}
      <div className="generation-section">
        <h3>1. Select Stories</h3>
        <div className="selection-controls">
          <button 
            onClick={handleSelectAllStories}
            className="select-all-button"
          >
            {selectedStories.size === stories.length ? 'Deselect All' : 'Select All'}
            ({stories.length} stories)
          </button>
          <span className="selection-count">
            {selectedStories.size} selected
          </span>
        </div>
        <div className="stories-grid">
          {stories.map((story) => (
            <div 
              key={story.id} 
              className={`story-card ${selectedStories.has(story.id) ? 'selected' : ''}`}
              onClick={() => handleStorySelect(story.id)}
            >
              <div className="story-header">
                <h4>{story.title}</h4>
                <div className="story-meta">
                  <span className="grade">Grade {story.grade_level}</span>
                  <span className={`difficulty difficulty-${story.difficulty}`}>
                    {story.difficulty}
                  </span>
                </div>
              </div>
              <div className="story-stats">
                <span>{story.word_count} words</span>
                <span>{story.estimated_reading_time}s reading</span>
                <span>{story.audio_count} existing audio</span>
              </div>
              {selectedStories.has(story.id) && (
                <div className="selected-indicator">✓</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Voice Selection */}
      <div className="generation-section">
        <h3>2. Select Voice Types</h3>
        <div className="selection-controls">
          <button 
            onClick={handleSelectAllVoices}
            className="select-all-button"
          >
            {selectedVoices.size === availableVoices.length ? 'Deselect All' : 'Select All'}
            ({availableVoices.length} voices)
          </button>
          <span className="selection-count">
            {selectedVoices.size} selected
          </span>
        </div>
        <div className="voices-grid">
          {availableVoices.map((voice) => (
            <div 
              key={voice.id} 
              className={`voice-card ${selectedVoices.has(voice.id) ? 'selected' : ''}`}
              onClick={() => handleVoiceSelect(voice.id)}
            >
              <div className="voice-header">
                <h4>{voice.name}</h4>
                {selectedVoices.has(voice.id) && (
                  <div className="selected-indicator">✓</div>
                )}
              </div>
              <p>{voice.description}</p>
              <button className="voice-preview" disabled>
                🔊 Preview (Coming Soon)
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Generation Summary */}
      {(selectedStories.size > 0 || selectedVoices.size > 0) && (
        <div className="generation-summary">
          <h3>3. Generation Summary</h3>
          <div className="summary-content">
            <div className="summary-item">
              <strong>Stories selected:</strong> {selectedStories.size}
            </div>
            <div className="summary-item">
              <strong>Voice types:</strong> {selectedVoices.size}
            </div>
            <div className="summary-item">
              <strong>Total files to generate:</strong> {calculateTotalFiles()}
            </div>
            <div className="summary-item">
              <strong>Estimated time:</strong> {estimateGenerationTime()}
            </div>
          </div>
          
          <div className="generation-actions">
            <button
              onClick={handleStartGeneration}
              disabled={isGenerating || selectedStories.size === 0 || selectedVoices.size === 0}
              className="start-generation-button"
            >
              {isGenerating ? 'Starting...' : '🎵 Start Generation'}
            </button>
          </div>
        </div>
      )}

      {/* Generation Jobs */}
      {generationJobs.length > 0 && (
        <div className="generation-jobs">
          <h3>Generation Jobs</h3>
          <div className="jobs-list">
            {generationJobs.map((job) => (
              <div key={job.id} className="job-card">
                <div className="job-header">
                  <div className="job-status">
                    <span className="status-icon">{getStatusIcon(job.status)}</span>
                    <span className="status-text">{job.status}</span>
                  </div>
                  <div className="job-meta">
                    Started: {new Date(job.startedAt).toLocaleString()}
                  </div>
                </div>
                
                <div className="job-details">
                  <div className="job-info">
                    <span>{job.stories.length} stories</span>
                    <span>{job.voiceTypes.length} voices</span>
                    <span>{job.totalFiles} total files</span>
                  </div>
                  
                  {job.status === 'processing' && (
                    <div className="job-progress">
                      <div className="progress-bar">
                        <div 
                          className="progress-fill" 
                          style={{width: `${job.progress}%`}}
                        ></div>
                      </div>
                      <div className="progress-text">
                        {job.completedFiles} / {job.totalFiles} files 
                        ({Math.round(job.progress)}%)
                      </div>
                    </div>
                  )}
                  
                  {job.status === 'completed' && (
                    <div className="job-completed">
                      <span>✅ All {job.totalFiles} audio files generated successfully!</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="coming-soon-notice">
        <h3>🚀 Enhanced Features Coming Soon</h3>
        <ul>
          <li>Voice preview and testing</li>
          <li>Custom voice speed and pitch settings</li>
          <li>Batch processing queue management</li>
          <li>Audio quality optimization options</li>
          <li>Integration with cloud TTS services</li>
          <li>Automatic retry for failed generations</li>
        </ul>
      </div>
    </div>
  );
};