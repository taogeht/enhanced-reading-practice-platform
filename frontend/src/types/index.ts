// Type definitions for the Reading Platform

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  user_type: 'student' | 'teacher' | 'admin';
  grade_level?: string;
  school?: string;
  date_joined: string;
}

export interface Story {
  id: number;
  title: string;
  content: string;
  grade_level: string;
  difficulty: 'easy' | 'medium' | 'hard';
  word_count: number;
  estimated_reading_time: number;
  audio_files: AudioFile[];
  created_at: string;
}

export interface StoryListItem {
  id: number;
  title: string;
  grade_level: string;
  difficulty: 'easy' | 'medium' | 'hard';
  word_count: number;
  estimated_reading_time: number;
  audio_count: number;
}

export interface AudioFile {
  id: number;
  voice_type: 'female_1' | 'female_2' | 'male_1' | 'male_2';
  file_path: string;
  duration: number;
  file_size: number;
}

export interface Assignment {
  id: number;
  title: string;
  description?: string;
  story: StoryListItem;
  teacher_name: string;
  assignment_code: string;
  due_date?: string;
  max_attempts: number;
  is_active: boolean;
  created_at: string;
}

export interface StudentAssignment {
  id: number;
  assignment_title: string;
  story_title: string;
  story_id: number;
  due_date?: string;
  attempts_used: number;
  is_completed: boolean;
  can_attempt: boolean;
  created_at: string;
}

export interface Recording {
  id: number;
  student_name: string;
  student_username: string;
  story_title: string;
  status: 'pending' | 'reviewed' | 'flagged';
  grade?: string;
  teacher_feedback?: string;
  duration: number | string;
  audio_file?: string;
  attempt_number: number;
  fluency_score?: number;
  accuracy_score?: number;
  created_at: string;
  updated_at?: string;
}

export interface RecordingReview {
  recording_id: number;
  feedback: string;
  grade: 'excellent' | 'good' | 'needs_practice';
  fluency_score: number;
  accuracy_score: number;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: User;
}

export interface ApiResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Phase 2 Types - Class Management

export interface Student {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  full_name: string;
  grade_level: string;
  email: string;
}

export interface Class {
  id: number;
  name: string;
  teacher: number;
  teacher_name: string;
  grade_level: string;
  school_year: string;
  student_count: number;
  students: Student[];
  is_active: boolean;
  created_at: string;
}

export interface ClassListItem {
  id: number;
  name: string;
  teacher_name: string;
  grade_level: string;
  school_year: string;
  student_count: number;
  is_active: boolean;
  created_at: string;
}

export interface AssignmentProgress {
  assignment: Assignment;
  progress: {
    total_students: number;
    completed: number;
    pending: number;
    completion_rate: number;
  };
  recordings: {
    total: number;
    reviewed: number;
    pending_review: number;
  };
}

export interface CreateClassAssignmentRequest {
  class_id: number;
  story_id: number;
  title: string;
  description?: string;
  due_date?: string;
  max_attempts?: number;
}