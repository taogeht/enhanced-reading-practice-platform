# Enhanced Reading Practice Platform

A comprehensive educational platform that leverages pre-generated TTS audio and unlimited student recording submissions to provide schools with a cost-effective, privacy-focused reading assessment solution.

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/taogeht/enhanced-reading-practice-platform)

## Project Structure

```
record-v3/
├── backend/          # Django/Python backend API
├── frontend/         # React frontend application
├── docs/            # Documentation
├── scripts/         # Deployment and utility scripts
├── PRD.md           # Product Requirements Document
└── README.md        # This file
```

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## Architecture

- **Frontend**: React application for teachers and students
- **Backend**: Django REST API with PostgreSQL database
- **Storage**: Cloud object storage for audio files and recordings
- **Authentication**: Django-based user management

## Development Phases

1. **Phase 1**: Foundation & Content Management (MVP)
2. **Phase 2**: Teacher Management Tools
3. **Phase 3**: Advanced Analytics

## API Endpoints

### Student Endpoints
- `GET /api/student/assignments` - Get assigned stories
- `POST /api/student/recordings` - Upload student recording

### Teacher Endpoints
- `GET /api/teacher/classes` - Get teacher's classes
- `POST /api/teacher/assignments` - Create new assignment
- `GET /api/teacher/recordings` - Get student submissions
- `PUT /api/teacher/recordings/:id/feedback` - Add feedback

### Audio Endpoints
- `GET /api/audio/:storyId/:voiceId` - Get static audio file
- `POST /api/teacher/audio/generate` - Generate bulk audio
