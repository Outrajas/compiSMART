# CompiSMART — Cross-Platform Content Intelligence RAG

## Overview

CompiSMART is a full-stack Retrieval-Augmented Generation (RAG) platform designed to analyze and compare YouTube videos and Instagram Reels.

The system ingests social media URLs, extracts metadata and transcripts, computes engagement analytics, generates semantic embeddings, stores transcript chunks in a vector database, and provides a conversational AI interface capable of comparative content analysis.

The project was built to satisfy the requirements of the Software Engineer Technical Challenge while emphasizing production architecture, scalability, cost-efficiency, caching, and dataset isolation.

---

# Features

## Cross-Platform Ingestion

Supports:

* YouTube Videos
* Instagram Reels

Automatically extracts:

* Title
* Creator
* Views
* Likes
* Comments
* Upload Date
* Duration
* Hashtags
* Follower Count (when available)
* Transcript

---

## Dynamic Analytics

Computes:

Engagement Rate

(likes + comments) / views × 100

Additional metrics:

* Hook Score
* Views per Follower Ratio
* Transcript Coverage
* Semantic Density
* Comparative Ranking

---

## Retrieval-Augmented Generation

Pipeline:

Video URL
↓
Transcript Extraction
↓
Chunking
↓
Embedding Generation
↓
Qdrant Vector Storage
↓
Semantic Retrieval
↓
LLM Reasoning

Built using:

* LangGraph
* LangChain
* Qdrant
* BGE Embeddings
* Groq LLM API

---

## Multi-Turn Conversational Analysis

Supports questions such as:

* Which video has the highest engagement rate?
* Compare opening hooks.
* Show transcript of the best-performing video.
* Why did Video A outperform Video B?
* Suggest improvements.

Features:

* Conversational Memory
* Source Attribution
* Transcript Retrieval
* Comparative Analytics

---

# Architecture

## Backend

FastAPI

Responsibilities:

* URL ingestion
* Metadata extraction
* Transcript processing
* Embedding generation
* RAG orchestration
* Analytics computation
* Dataset isolation

---

## Frontend

React + Vite

Responsibilities:

* URL submission
* Dataset management
* Analytics visualization
* Chat interface
* Transcript inspection

---

## Storage Layer

SQLite

Stores:

* Cached video metadata
* Cached transcripts
* Dataset mappings
* Chat history
* Analytics cache

Qdrant

Stores:

* Semantic transcript chunks
* Vector embeddings

---

# Dataset Isolation System

One major engineering challenge discovered during development was contamination between analysis sessions.

Problem:

Videos analyzed previously appeared in future analytics and chat responses.

Example:

Dataset A:

* Omni-Man
* Doctor Mike

Dataset B:

* Messi
* Cristiano

Expected:

Dataset B should only analyze:

* Messi
* Cristiano

Observed:

Chat and analytics occasionally referenced Dataset A.

Solution:

Introduced:

datasets
dataset_videos

mapping tables.

Permanent cache remains global.

Analytics, retrieval, rankings, transcripts, and chat context are filtered using the active dataset only.

This enables:

* Cache reuse
* Session isolation
* Accurate analytics

without reprocessing existing videos.

---

# Caching Strategy

To minimize cost and latency:

Video Metadata Cache

Stores:

* metadata
* transcript
* analytics

Transcript Embedding Cache

Avoids re-embedding previously processed videos.

Answer Cache

Stores previous LLM responses for repeated dataset-specific questions.

Benefits:

* Reduced Groq usage
* Reduced embedding generation
* Faster response times

---

# Performance Optimizations

Implemented:

* Parallel ingestion
* Cache-first retrieval
* Dataset-scoped querying
* Qdrant vector filtering
* Persistent analytics storage

Current optimization roadmap:

* Startup model preloading
* Batch embedding generation
* Async ingestion pipeline
* Request deduplication
* Redis answer caching
* PostgreSQL migration

Target:

Sub-10 second end-to-end analysis for previously unseen videos.

---

# Instagram Challenges & Engineering Decisions

Instagram is significantly harder to ingest than YouTube due to:

* Frequent API restrictions
* GraphQL rate limits
* Anonymous access limitations

Implemented strategy:

1. yt-dlp metadata extraction
2. Instaloader enrichment
3. Fallback transcript extraction
4. Cache persistence

Follower count retrieval was intentionally degraded gracefully when Instagram blocks profile queries.

System continues functioning without failure.

---

# Debugging Challenges Solved

## Missing Models Package

Issue:

ModuleNotFoundError: app.models

Resolution:

Rebuilt models package and restored schema imports.

---

## SQLite Schema Drift

Issue:

Missing tables after repository rollback.

Resolution:

Implemented startup database initialization and migration-safe table creation.

---

## Session Contamination

Issue:

Analytics mixed unrelated videos.

Resolution:

Dataset isolation architecture.

---

## Instagram Transcript Failures

Issue:

Whisper fallback generator errors and Instagram restrictions.

Resolution:

Introduced platform-specific extraction routing and cache-first behavior.

---

## Deployment Challenges

Issue:

Railway deployment generated a 2.8GB container image due to:

* Torch
* Transformers
* Whisper
* CUDA dependencies

Resolution:

Identified heavy runtime dependencies and prepared deployment optimization plan.

---

# Scalability Discussion

## Current Version

Designed for:

* Demonstrations
* Research
* Small creator workflows

Supports:

* Hundreds of videos
* Cached semantic search
* Multi-dataset comparisons

---

## Scaling to 1000 Creators per Day

Recommended production architecture:

Frontend:

* Next.js

Backend:

* FastAPI

Database:

* PostgreSQL

Vector Store:

* Qdrant Cloud

Caching:

* Redis

Queue:

* Celery / RabbitMQ

Embeddings:

* Dedicated embedding service

Object Storage:

* S3

Benefits:

* Horizontal scaling
* Reduced inference costs
* High cache hit rates
* Lower retrieval latency

---

# Tech Stack

Frontend:

* React
* Vite
* Tailwind

Backend:

* FastAPI

RAG:

* LangGraph
* LangChain

Embeddings:

* BAAI/bge-small-en-v1.5

Vector Database:

* Qdrant

LLM:

* Groq

Metadata Extraction:

* yt-dlp
* Instaloader

Database:

* SQLite

---

# Running Locally

Backend

pip install -r requirements.txt

uvicorn app.main:app --reload

Frontend

npm install

npm run dev

---

# Environment Variables

Create .env

GROQ_API_KEY=

HF_TOKEN=

QDRANT_URL=

QDRANT_API_KEY=

---

# Future Improvements

* PostgreSQL migration
* Redis caching
* Streaming responses
* Incremental embeddings
* GPU inference support
* Multi-platform expansion
* Creator benchmarking dashboards

---

# Conclusion

CompiSMART demonstrates a complete end-to-end RAG architecture capable of ingesting, analyzing, comparing, and reasoning over social media content across platforms.

The project emphasizes engineering tradeoffs, caching, scalability, dataset isolation, retrieval accuracy, and production-oriented design rather than simple prompt engineering.
