# ProfPilot

## AI-Powered Academic Companion for Faculty

ProfPilot is an AI-first academic platform designed to help university lecturers manage and reason about their academic environment.

Rather than functioning as a generic chatbot or a standalone attendance application, ProfPilot is being developed around structured academic data, persistent context, academic memory, domain-specific reasoning, prediction, recommendations, and workflow automation.

## Current Features

- Faculty-oriented mobile application
- Course and syllabus management
- Faculty schedule and timetable
- Dynamic course workspace
- Academic progress tracking
- Academic context engine
- Persistent academic event memory
- Context-aware AI queries
- Basic syllabus completion prediction
- Basic academic what-if reasoning
- Academic progress alerts
- Faculty community prototype

## Architecture

```text
React Native + Expo
        |
        v
     FastAPI
        |
   +----+----+
   |         |
 SQLite   AI Services
             |
      +------+------+
      |             |
 Academic       Memory
 Context        System
      |             |
      +------+------+
             |
         AI Reasoning
Technology Stack
Mobile
React Native
Expo
TypeScript
Expo Router
Backend
Python
FastAPI
SQLAlchemy
SQLite
AI
Academic context engine
Persistent academic memory
Rule-based reasoning prototypes
Planned custom NLP / ML components
Planned semantic retrieval and prediction systems
Project Structure
ProfPilot/
├── backend/
│   ├── app/
│   │   ├── database/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   └── services/
│   ├── seed/
│   └── requirements.txt
│
├── mobile/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── config/
│   │   ├── data/
│   │   └── services/
│   └── package.json
│
├── data/
├── docs/
├── .gitignore
└── README.md
Current AI Pipeline
User Query
    |
    v
Academic Context
    +
Persistent Memory
    |
    v
Reasoning
    |
    v
AI Response
Roadmap
Intelligent memory relevance retrieval
Custom intent classification
Entity extraction
Lecture-to-syllabus semantic mapping
Improved syllabus prediction
Academic recommendations
Advanced what-if simulation
Faculty workflow automation
Semantic faculty/resource discovery
Voice interaction
Optional vision/OCR capabilities
Development Status

ProfPilot is currently under active development as a university academic project.

This repository represents the current development version and is expected to evolve significantly as the custom AI layer is implemented.