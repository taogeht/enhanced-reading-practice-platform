// Recording Review component for teachers - Phase 2

import React, { useState, useEffect } from 'react';
import { Recording } from '../types';
import { recordingsAPI } from '../services/api';

export const RecordingReviewComponent: React.FC = () => {
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedRecording, setSelectedRecording] = useState<Recording | null>(null);
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [reviewForm, setReviewForm] = useState({
    feedback: '',
    grade: 'good' as 'excellent' | 'good' | 'needs_practice',
    fluency_score: 3,
    accuracy_score: 3
  });
  const [submitLoading, setSubmitLoading] = useState(false);

  useEffect(() => {
    loadRecordings();
  }, []);

  const loadRecordings = async () => {
    try {
      setLoading(true);
      const response = await recordingsAPI.getTeacherRecordings?.();
      if (response) {
        setRecordings(response.results || []);
      }
    } catch (err: any) {
      setError('Failed to load recordings for review.');
      console.error('Recording load error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePlayRecording = (recording: Recording) => {
    if (currentAudio) {
      currentAudio.pause();
      setCurrentAudio(null);
      setIsPlaying(false);
    }

    if (recording.audio_file) {
      const audio = new Audio(recording.audio_file);
      audio.onplay = () => setIsPlaying(true);
      audio.onpause = () => setIsPlaying(false);
      audio.onended = () => {
        setIsPlaying(false);
        setCurrentAudio(null);
      };
      audio.play();
      setCurrentAudio(audio);
    }
  };

  const handleStopRecording = () => {
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.currentTime = 0;
      setCurrentAudio(null);
      setIsPlaying(false);
    }
  };

  const handleSelectRecording = (recording: Recording) => {
    setSelectedRecording(recording);
    setReviewForm({
      feedback: '',
      grade: 'good',
      fluency_score: 3,
      accuracy_score: 3
    });
    if (currentAudio) {
      currentAudio.pause();
      setCurrentAudio(null);
      setIsPlaying(false);
    }
  };

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRecording) return;

    try {
      setSubmitLoading(true);
      await recordingsAPI.submitReview?.(selectedRecording.id, {
        ...reviewForm,
        recording_id: selectedRecording.id
      });

      // Update recording status
      setRecordings(prev => 
        prev.map(r => 
          r.id === selectedRecording.id 
            ? { ...r, status: 'reviewed', teacher_feedback: reviewForm.feedback }
            : r
        )
      );

      setSelectedRecording(null);
    } catch (err: any) {
      setError('Failed to submit review. Please try again.');
      console.error('Review submission error:', err);
    } finally {
      setSubmitLoading(false);
    }
  };

  const pendingRecordings = recordings.filter(r => r.status === 'pending');
  const reviewedRecordings = recordings.filter(r => r.status === 'reviewed');

  if (loading) {
    return <div className="loading">Loading recordings...</div>;
  }

  return (
    <div className="recording-review">
      <div className="section-header">
        <h2>Review Student Recordings</h2>
        <div className="review-stats">
          <span className="stat">
            {pendingRecordings.length} Pending Reviews
          </span>
          <span className="stat">
            {reviewedRecordings.length} Completed
          </span>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Review Modal */}
      {selectedRecording && (
        <div className="modal-overlay">
          <div className="modal large">
            <div className="modal-header">
              <h3>Review Recording</h3>
              <button 
                className="close-button"
                onClick={() => setSelectedRecording(null)}
              >
                ×
              </button>
            </div>
            
            <div className="recording-review-content">
              <div className="student-submission">
                <div className="submission-header">
                  <div className="student-info">
                    <h4>{selectedRecording.student_name}</h4>
                    <span className="story-title">{selectedRecording.story_title}</span>
                    <span className="submission-time">
                      Submitted: {new Date(selectedRecording.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div className="audio-controls">
                    <button
                      onClick={() => handlePlayRecording(selectedRecording)}
                      disabled={!selectedRecording.audio_file}
                      className={`play-button ${isPlaying ? 'playing' : ''}`}
                    >
                      {isPlaying ? '⏸ Pause' : '▶ Play Recording'}
                    </button>
                    {isPlaying && (
                      <button onClick={handleStopRecording} className="stop-button">
                        ⏹ Stop
                      </button>
                    )}
                    <span className="duration">
                      Duration: {selectedRecording.duration || 'Unknown'}
                    </span>
                  </div>
                </div>
              </div>

              <form onSubmit={handleSubmitReview} className="review-form">
                <div className="form-section">
                  <h4>Assessment Scores</h4>
                  <div className="score-controls">
                    <div className="score-item">
                      <label htmlFor="fluency-score">Fluency (1-5):</label>
                      <select
                        id="fluency-score"
                        value={reviewForm.fluency_score}
                        onChange={(e) => setReviewForm({
                          ...reviewForm,
                          fluency_score: Number(e.target.value)
                        })}
                      >
                        <option value={1}>1 - Needs significant improvement</option>
                        <option value={2}>2 - Below average</option>
                        <option value={3}>3 - Average</option>
                        <option value={4}>4 - Good</option>
                        <option value={5}>5 - Excellent</option>
                      </select>
                    </div>
                    <div className="score-item">
                      <label htmlFor="accuracy-score">Accuracy (1-5):</label>
                      <select
                        id="accuracy-score"
                        value={reviewForm.accuracy_score}
                        onChange={(e) => setReviewForm({
                          ...reviewForm,
                          accuracy_score: Number(e.target.value)
                        })}
                      >
                        <option value={1}>1 - Many errors</option>
                        <option value={2}>2 - Several errors</option>
                        <option value={3}>3 - Some errors</option>
                        <option value={4}>4 - Few errors</option>
                        <option value={5}>5 - No errors</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div className="form-section">
                  <h4>Overall Grade</h4>
                  <div className="grade-selection">
                    <label>
                      <input
                        type="radio"
                        name="grade"
                        value="excellent"
                        checked={reviewForm.grade === 'excellent'}
                        onChange={(e) => setReviewForm({
                          ...reviewForm,
                          grade: e.target.value as any
                        })}
                      />
                      🌟 Excellent
                    </label>
                    <label>
                      <input
                        type="radio"
                        name="grade"
                        value="good"
                        checked={reviewForm.grade === 'good'}
                        onChange={(e) => setReviewForm({
                          ...reviewForm,
                          grade: e.target.value as any
                        })}
                      />
                      👍 Good
                    </label>
                    <label>
                      <input
                        type="radio"
                        name="grade"
                        value="needs_practice"
                        checked={reviewForm.grade === 'needs_practice'}
                        onChange={(e) => setReviewForm({
                          ...reviewForm,
                          grade: e.target.value as any
                        })}
                      />
                      📚 Needs Practice
                    </label>
                  </div>
                </div>

                <div className="form-section">
                  <label htmlFor="feedback">Feedback for Student:</label>
                  <textarea
                    id="feedback"
                    value={reviewForm.feedback}
                    onChange={(e) => setReviewForm({
                      ...reviewForm,
                      feedback: e.target.value
                    })}
                    placeholder="Provide constructive feedback to help the student improve..."
                    rows={4}
                    required
                  />
                </div>

                <div className="form-actions">
                  <button
                    type="button"
                    onClick={() => setSelectedRecording(null)}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitLoading || !reviewForm.feedback.trim()}
                    className="submit-review-button"
                  >
                    {submitLoading ? 'Submitting...' : 'Submit Review'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Recordings Lists */}
      <div className="recordings-section">
        {pendingRecordings.length > 0 ? (
          <>
            <h3>Pending Reviews ({pendingRecordings.length})</h3>
            <div className="recordings-grid">
              {pendingRecordings.map((recording) => (
                <div key={recording.id} className="recording-card pending">
                  <div className="recording-header">
                    <h4>{recording.student_name}</h4>
                    <span className="status-badge pending">Pending</span>
                  </div>
                  <div className="recording-info">
                    <div className="info-item">
                      <strong>Story:</strong> {recording.story_title}
                    </div>
                    <div className="info-item">
                      <strong>Submitted:</strong> {new Date(recording.created_at).toLocaleDateString()}
                    </div>
                    <div className="info-item">
                      <strong>Attempt:</strong> {recording.attempt_number}
                    </div>
                  </div>
                  <div className="recording-actions">
                    <button
                      onClick={() => handleSelectRecording(recording)}
                      className="review-button primary"
                    >
                      📝 Review
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="empty-state">
            <h3>🎉 All caught up!</h3>
            <p>No recordings waiting for review.</p>
          </div>
        )}

        {reviewedRecordings.length > 0 && (
          <>
            <h3>Recently Reviewed ({reviewedRecordings.length})</h3>
            <div className="recordings-grid">
              {reviewedRecordings.slice(0, 6).map((recording) => (
                <div key={recording.id} className="recording-card reviewed">
                  <div className="recording-header">
                    <h4>{recording.student_name}</h4>
                    <span className="status-badge reviewed">Reviewed</span>
                  </div>
                  <div className="recording-info">
                    <div className="info-item">
                      <strong>Story:</strong> {recording.story_title}
                    </div>
                    <div className="info-item">
                      <strong>Reviewed:</strong> {new Date(recording.updated_at || recording.created_at).toLocaleDateString()}
                    </div>
                    {recording.teacher_feedback && (
                      <div className="feedback-preview">
                        <strong>Feedback:</strong> {recording.teacher_feedback.length > 50 
                          ? `${recording.teacher_feedback.substring(0, 50)}...` 
                          : recording.teacher_feedback}
                      </div>
                    )}
                  </div>
                  <div className="recording-actions">
                    <button
                      onClick={() => handleSelectRecording(recording)}
                      className="view-button"
                    >
                      👁 View Review
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};