// Class Management component for teachers

import React, { useState } from 'react';
import { ClassListItem, Class, Student } from '../types';
import { classAPI } from '../services/api';

interface ClassManagementProps {
  classes: ClassListItem[];
  onClassesChange: (classes: ClassListItem[]) => void;
}

export const ClassManagement: React.FC<ClassManagementProps> = ({ classes, onClassesChange }) => {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedClass, setSelectedClass] = useState<Class | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Create new class form state
  const [newClass, setNewClass] = useState({
    name: '',
    grade_level: '1',
    school_year: '2024-2025',
    is_active: true
  });

  // Student search state
  const [studentSearchQuery, setStudentSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Student[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);

  const handleCreateClass = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const createdClass = await classAPI.createClass(newClass);
      
      // Convert to ClassListItem format
      const newClassItem: ClassListItem = {
        id: createdClass.id,
        name: createdClass.name,
        teacher_name: createdClass.teacher_name,
        grade_level: createdClass.grade_level,
        school_year: createdClass.school_year,
        student_count: 0,
        is_active: createdClass.is_active,
        created_at: createdClass.created_at
      };
      
      onClassesChange([newClassItem, ...classes]);
      setNewClass({ name: '', grade_level: '1', school_year: '2024-2025', is_active: true });
      setShowCreateForm(false);
      
    } catch (err: any) {
      setError('Failed to create class. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleViewClass = async (classItem: ClassListItem) => {
    try {
      setLoading(true);
      const fullClass = await classAPI.getClass(classItem.id);
      setSelectedClass(fullClass);
    } catch (err: any) {
      setError('Failed to load class details.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearchStudents = async (query: string) => {
    if (query.length < 2) {
      setSearchResults([]);
      return;
    }
    
    try {
      setSearchLoading(true);
      const response = await classAPI.searchStudents(query);
      setSearchResults(response.results);
    } catch (err) {
      console.error('Search error:', err);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleAddStudent = async (student: Student) => {
    if (!selectedClass) return;
    
    try {
      await classAPI.addStudentToClass(selectedClass.id, student.id);
      
      // Refresh class details
      const updatedClass = await classAPI.getClass(selectedClass.id);
      setSelectedClass(updatedClass);
      
      // Update the classes list
      const updatedClasses = classes.map(c => 
        c.id === selectedClass.id 
          ? { ...c, student_count: updatedClass.student_count }
          : c
      );
      onClassesChange(updatedClasses);
      
      setStudentSearchQuery('');
      setSearchResults([]);
      
    } catch (err: any) {
      setError('Failed to add student to class.');
    }
  };

  const handleRemoveStudent = async (studentId: number) => {
    if (!selectedClass) return;
    
    try {
      await classAPI.removeStudentFromClass(selectedClass.id, studentId);
      
      // Refresh class details
      const updatedClass = await classAPI.getClass(selectedClass.id);
      setSelectedClass(updatedClass);
      
      // Update the classes list
      const updatedClasses = classes.map(c => 
        c.id === selectedClass.id 
          ? { ...c, student_count: updatedClass.student_count }
          : c
      );
      onClassesChange(updatedClasses);
      
    } catch (err: any) {
      setError('Failed to remove student from class.');
    }
  };

  return (
    <div className="class-management">
      <div className="section-header">
        <h2>Class Management</h2>
        <button 
          className="create-button"
          onClick={() => setShowCreateForm(true)}
        >
          + Create New Class
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Create Class Modal */}
      {showCreateForm && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h3>Create New Class</h3>
              <button 
                className="close-button"
                onClick={() => setShowCreateForm(false)}
              >
                ×
              </button>
            </div>
            
            <form onSubmit={handleCreateClass}>
              <div className="form-group">
                <label htmlFor="class-name">Class Name:</label>
                <input
                  id="class-name"
                  type="text"
                  value={newClass.name}
                  onChange={(e) => setNewClass({ ...newClass, name: e.target.value })}
                  placeholder="e.g., Grade 1A - Reading"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="grade-level">Grade Level:</label>
                <select
                  id="grade-level"
                  value={newClass.grade_level}
                  onChange={(e) => setNewClass({ ...newClass, grade_level: e.target.value })}
                >
                  <option value="K">Kindergarten</option>
                  <option value="1">Grade 1</option>
                  <option value="2">Grade 2</option>
                  <option value="3">Grade 3</option>
                  <option value="4">Grade 4</option>
                  <option value="5">Grade 5</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="school-year">School Year:</label>
                <input
                  id="school-year"
                  type="text"
                  value={newClass.school_year}
                  onChange={(e) => setNewClass({ ...newClass, school_year: e.target.value })}
                  placeholder="2024-2025"
                />
              </div>

              <div className="modal-actions">
                <button type="button" onClick={() => setShowCreateForm(false)}>
                  Cancel
                </button>
                <button type="submit" disabled={loading}>
                  {loading ? 'Creating...' : 'Create Class'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Class Details Modal */}
      {selectedClass && (
        <div className="modal-overlay">
          <div className="modal large">
            <div className="modal-header">
              <h3>{selectedClass.name}</h3>
              <button 
                className="close-button"
                onClick={() => setSelectedClass(null)}
              >
                ×
              </button>
            </div>
            
            <div className="class-details">
              <div className="class-info">
                <p><strong>Grade Level:</strong> {selectedClass.grade_level}</p>
                <p><strong>School Year:</strong> {selectedClass.school_year}</p>
                <p><strong>Students:</strong> {selectedClass.student_count}</p>
              </div>

              {/* Add Student Section */}
              <div className="add-student-section">
                <h4>Add Students</h4>
                <div className="student-search">
                  <input
                    type="text"
                    placeholder="Search students by username..."
                    value={studentSearchQuery}
                    onChange={(e) => {
                      setStudentSearchQuery(e.target.value);
                      handleSearchStudents(e.target.value);
                    }}
                  />
                  {searchLoading && <span>Searching...</span>}
                </div>
                
                {searchResults.length > 0 && (
                  <div className="search-results">
                    {searchResults.map((student) => (
                      <div key={student.id} className="search-result">
                        <span>{student.full_name} ({student.username})</span>
                        <button
                          onClick={() => handleAddStudent(student)}
                          className="add-student-button"
                        >
                          Add
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Students List */}
              <div className="students-list">
                <h4>Class Students</h4>
                {selectedClass.students.length === 0 ? (
                  <p>No students in this class yet.</p>
                ) : (
                  <div className="students-grid">
                    {selectedClass.students.map((student) => (
                      <div key={student.id} className="student-card">
                        <div className="student-info">
                          <strong>{student.full_name}</strong>
                          <span>@{student.username}</span>
                          <span>Grade {student.grade_level}</span>
                        </div>
                        <button
                          onClick={() => handleRemoveStudent(student.id)}
                          className="remove-student-button"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Classes List */}
      <div className="classes-list">
        {classes.length === 0 ? (
          <div className="empty-state">
            <p>No classes created yet. Create your first class to get started!</p>
          </div>
        ) : (
          <div className="classes-grid">
            {classes.map((classItem) => (
              <div key={classItem.id} className="class-card">
                <div className="class-header">
                  <h3>{classItem.name}</h3>
                  <span className="grade-badge">Grade {classItem.grade_level}</span>
                </div>
                
                <div className="class-details-summary">
                  <div className="detail-item">
                    <span className="label">Students:</span>
                    <span className="value">{classItem.student_count}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">School Year:</span>
                    <span className="value">{classItem.school_year}</span>
                  </div>
                  <div className="detail-item">
                    <span className="label">Created:</span>
                    <span className="value">
                      {new Date(classItem.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                
                <div className="class-actions">
                  <button
                    onClick={() => handleViewClass(classItem)}
                    className="manage-button"
                  >
                    Manage Students
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};