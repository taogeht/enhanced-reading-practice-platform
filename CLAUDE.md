# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
Enhanced Reading Practice Platform - A comprehensive educational platform that leverages pre-generated TTS audio and student recording submissions for reading assessment.

## Development Commands

### Backend (Django/Python)
```bash
cd backend
source venv/bin/activate  # Activate virtual environment
pip install -r requirements.txt  # Install dependencies
python manage.py migrate  # Apply database migrations
python manage.py runserver  # Start development server (port 8000)
python manage.py makemigrations  # Create new migrations after model changes
```

### Frontend (React/TypeScript)
```bash
cd frontend
npm install  # Install dependencies  
npm start    # Start development server (port 3000)
npm run build  # Build for production
npm test     # Run tests
```

## Project Structure
```
record-v3/
├── backend/              # Django REST API
│   ├── authentication/   # Custom user model and auth
│   ├── stories/         # Story content and audio files
│   ├── recordings/      # Student recording submissions
│   ├── assignments/     # Teacher assignment management
│   └── reading_platform/ # Main Django project
├── frontend/            # React TypeScript application
├── docs/               # Documentation
├── scripts/           # Deployment and utility scripts
└── PRD.md            # Product Requirements Document
```

## Architecture
- **Frontend**: React with TypeScript for type safety
- **Backend**: Django REST Framework with PostgreSQL (SQLite for development)
- **Storage**: Planned cloud object storage for audio files
- **Authentication**: Custom Django User model supporting teachers, students, and admins

## Database Models
- **User**: Custom user model with roles (teacher, student, admin)
- **Story**: Educational content with grade levels and difficulty
- **AudioFile**: Pre-generated TTS audio files for stories
- **Assignment**: Teacher-created reading assignments
- **Recording**: Student audio submissions with teacher feedback
- **StudentAssignment**: Tracks student assignment progress

## API Design
Following RESTful conventions with endpoints for:
- Student: `/api/student/assignments`, `/api/student/recordings`
- Teacher: `/api/teacher/classes`, `/api/teacher/assignments`, `/api/teacher/recordings`
- Audio: `/api/audio/:storyId/:voiceId`

## Development Phases
1. **Phase 1**: Foundation & Content Management (MVP) - ✅ **COMPLETED**
   - ✅ Custom User model with teacher/student roles
   - ✅ Story content management with audio file support
   - ✅ Student assignment system
   - ✅ Audio recording and submission functionality
   - ✅ Complete student workflow (login → assignments → read story → record)
   - ✅ Django admin interface for content management
   - ✅ Responsive React frontend with TypeScript
2. **Phase 2**: Teacher Management Tools - *Planned*
3. **Phase 3**: Advanced Analytics - *Planned*

## Key Technical Decisions
- Using custom User model to support multiple user types
- Pre-generated TTS audio to eliminate API costs and ensure performance
- Microservices-oriented architecture for scalability
- TypeScript for frontend type safety