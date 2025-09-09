// API service for communicating with the Django backend

import axios from 'axios';
import {
  User,
  Story,
  StoryListItem,
  StudentAssignment,
  Recording,
  LoginCredentials,
  LoginResponse,
  ApiResponse,
  Class,
  ClassListItem,
  Student,
  AssignmentProgress,
  CreateClassAssignmentRequest
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

// Auth API
export const authAPI = {
  login: async (credentials: LoginCredentials): Promise<LoginResponse> => {
    const response = await api.post('/auth/login/', credentials);
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post('/auth/logout/');
    localStorage.removeItem('authToken');
  },

  getProfile: async (): Promise<User> => {
    const response = await api.get('/auth/profile/');
    return response.data;
  },
};

// Stories API
export const storiesAPI = {
  getStories: async (gradeLevel?: string): Promise<ApiResponse<StoryListItem>> => {
    const params = gradeLevel ? { grade_level: gradeLevel } : {};
    const response = await api.get('/stories/', { params });
    return response.data;
  },

  getStory: async (id: number): Promise<Story> => {
    const response = await api.get(`/stories/${id}/`);
    return response.data;
  },

  getAudioUrl: (storyId: number, voiceType: string): string => {
    return `${API_BASE_URL}/stories/${storyId}/audio/${voiceType}/`;
  },
};

// Assignments API
export const assignmentsAPI = {
  getStudentAssignments: async (): Promise<ApiResponse<StudentAssignment>> => {
    const response = await api.get('/assignments/student/');
    return response.data;
  },

  joinAssignment: async (assignmentCode: string): Promise<{ message: string }> => {
    const response = await api.post('/assignments/join/', { assignment_code: assignmentCode });
    return response.data;
  },

  getAssignments: async (): Promise<ApiResponse<any>> => {
    const response = await api.get('/assignments/');
    return response.data;
  },
};

// Recordings API
export const recordingsAPI = {
  getStudentRecordings: async (): Promise<ApiResponse<Recording>> => {
    const response = await api.get('/recordings/student/');
    return response.data;
  },

  uploadRecording: async (formData: FormData): Promise<Recording> => {
    const response = await api.post('/recordings/student/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // Teacher recording review methods
  getTeacherRecordings: async (): Promise<ApiResponse<Recording>> => {
    const response = await api.get('/recordings/teacher/');
    return response.data;
  },

  submitReview: async (recordingId: number, reviewData: any): Promise<{ message: string }> => {
    const response = await api.post(`/recordings/${recordingId}/review/`, reviewData);
    return response.data;
  },
};

// Phase 2 APIs - Class Management

export const classAPI = {
  getClasses: async (): Promise<ApiResponse<ClassListItem>> => {
    const response = await api.get('/auth/classes/');
    return response.data;
  },

  getClass: async (id: number): Promise<Class> => {
    const response = await api.get(`/auth/classes/${id}/`);
    return response.data;
  },

  createClass: async (classData: Omit<Class, 'id' | 'teacher' | 'teacher_name' | 'student_count' | 'students' | 'created_at'>): Promise<Class> => {
    const response = await api.post('/auth/classes/', classData);
    return response.data;
  },

  updateClass: async (id: number, classData: Partial<Class>): Promise<Class> => {
    const response = await api.put(`/auth/classes/${id}/`, classData);
    return response.data;
  },

  addStudentToClass: async (classId: number, studentId: number): Promise<{ message: string }> => {
    const response = await api.post(`/auth/classes/${classId}/add-student/`, { student_id: studentId });
    return response.data;
  },

  removeStudentFromClass: async (classId: number, studentId: number): Promise<{ message: string }> => {
    const response = await api.delete(`/auth/classes/${classId}/remove-student/${studentId}/`);
    return response.data;
  },

  searchStudents: async (query: string): Promise<{ results: Student[] }> => {
    const response = await api.get(`/auth/search-students/?q=${encodeURIComponent(query)}`);
    return response.data;
  },
};

// Enhanced Assignment APIs for Phase 2
export const teacherAssignmentAPI = {
  createClassAssignment: async (assignmentData: CreateClassAssignmentRequest): Promise<{ message: string; assignment: any }> => {
    const response = await api.post('/assignments/create-class-assignment/', assignmentData);
    return response.data;
  },

  getAssignmentProgress: async (assignmentId: number): Promise<AssignmentProgress> => {
    const response = await api.get(`/assignments/${assignmentId}/progress/`);
    return response.data;
  },
};

// Analytics API for Phase 3
export const analyticsAPI = {
  getStudentFlags: async (): Promise<ApiResponse<any>> => {
    const response = await api.get('/analytics/flags/');
    return response.data;
  },

  getStudentAnalytics: async (): Promise<ApiResponse<any>> => {
    const response = await api.get('/analytics/student-analytics/');
    return response.data;
  },

  getSystemAnalytics: async (): Promise<ApiResponse<any>> => {
    const response = await api.get('/analytics/system-analytics/');
    return response.data;
  },

  getDashboardSummary: async (): Promise<any> => {
    const response = await api.get('/analytics/dashboard-summary/');
    return response.data;
  },

  resolveFlag: async (flagId: number, notes?: string): Promise<{ message: string }> => {
    const response = await api.post(`/analytics/flags/${flagId}/resolve/`, { 
      resolution_notes: notes || '' 
    });
    return response.data;
  },

  triggerAnalysis: async (): Promise<{ message: string }> => {
    const response = await api.post('/analytics/trigger-analysis/');
    return response.data;
  },

  getAvailableReports: async (): Promise<{ available_reports: any[] }> => {
    const response = await api.get('/analytics/reports/available/');
    return response.data;
  },
};

export default api;