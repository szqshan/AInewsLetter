# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### MinIO File Manager Backend

```bash
# Navigate to backend
cd minio-file-manager/backend

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
python -m uvicorn app.main:app --reload --port 9011

# Access API documentation
# Swagger UI: http://localhost:9011/docs
# ReDoc: http://localhost:9011/redoc
```

### MinIO File Manager Frontend

```bash
# Navigate to frontend
cd minio-file-manager/frontend

# Install dependencies
npm install

# Run development server
npm run dev  # Runs on http://localhost:9010

# Build for production
npm run build
```

### Newsletter Upload to Elasticsearch

```bash
# Test Newsletter upload functionality
python minio-file-manager/backend/test_newsletter_upload.py

# Upload articles from crawler data
python minio-file-manager/backend/upload_crawled_articles.py [JSON_FILE] --verify

# Batch upload with custom size
python minio-file-manager/backend/upload_crawled_articles.py articles.json --batch-size 50
```

### Testing MinIO APIs

```bash
# Test bucket operations
python minio-file-manager/backend/test_public_bucket.py

# Test public URL generation
python minio-file-manager/backend/test_public_url.py

# Test delete operations
python minio-file-manager/backend/test_delete_api.py
```

## Architecture Overview

This project integrates MinIO object storage with Elasticsearch for Newsletter article management. It consists of two main components:

### 1. MinIO File Manager
A full-stack application for managing files in MinIO storage:

**Backend (FastAPI)**:
- `app/services/minio_service.py`: Core MinIO operations (singleton pattern)
- `app/services/elasticsearch_service.py`: Basic ES integration for file metadata
- `app/services/newsletter_elasticsearch_service.py`: Specialized Newsletter article indexing with deduplication
- `app/api/endpoints/`: RESTful endpoints for buckets, objects, search, and newsletter operations

**Frontend (Next.js 15 + React 19)**:
- Modern UI with Tailwind CSS and shadcn/ui components
- Zustand for state management
- Drag-and-drop file upload support

### 2. Newsletter Article System
Specialized system for managing Newsletter articles with Elasticsearch integration:

**Key Features**:
- **Deduplication**: Uses content_hash (SHA256) and article ID to prevent duplicates
- **Multi-dimensional Scoring**: Calculates popularity, freshness, quality, and combined scores
- **Advanced Search**: Full-text search with field boosting, tag filtering, date ranges
- **Recommendations**: Similar articles (More Like This), trending articles

**Elasticsearch Index Structure**:
- Index: `newsletter_articles`
- Custom analyzers: English analyzer with synonyms, N-gram analyzer for fuzzy matching
- Nested tags structure for complex queries
- Dense vector field (384 dims) prepared for future embeddings

## Data Flow

### Article Upload Pipeline
1. **Source**: Crawler output from `/Users/ruanchuhao/Downloads/Codes/NewsLetters/爬虫mlp`
2. **Processing**: Article data with metadata and local images
3. **Deduplication**: Check by ID and content hash
4. **Score Calculation**: Popularity, freshness, quality scores
5. **Storage**: 
   - Optional: MinIO for raw JSON files
   - Required: Elasticsearch for searchable index

### API Integration Points

**Newsletter Endpoints** (`/api/v1/newsletter/`):
- `POST /upload-article`: Single article with dedup check
- `POST /bulk-upload`: Batch upload with progress tracking
- `POST /search`: Advanced search with multiple filters
- `GET /article/{id}/similar`: Find similar articles
- `GET /trending`: Get popular articles by time range
- `GET /statistics`: Aggregated statistics

**MinIO Endpoints** (`/api/v1/`):
- Bucket management: create, delete, list, set public/private
- Object operations: upload, download, copy, delete
- URL generation: public URLs and presigned URLs

## Configuration

### Backend Configuration (.env)
```env
# MinIO Settings
MINIO_ENDPOINT=60.205.160.74:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_USE_SSL=false

# Elasticsearch Settings
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX=minio_files
ELASTICSEARCH_USE_SSL=false

# API Settings
API_HOST=0.0.0.0
API_PORT=9011
```

### Newsletter Article Structure
Articles from the crawler follow this structure:
```python
{
    "id": int,                      # Unique identifier
    "title": str,                   # Article title
    "subtitle": str,                # Subtitle
    "content": str,                 # Full content (optional)
    "post_date": str,              # ISO format date
    "type": str,                   # newsletter/tutorial/paper
    "wordcount": int,              # Word count
    "reactions": dict,             # {"❤": count}
    "postTags": list,              # [{"id", "name", "slug"}]
    "local_images": list,          # Image metadata
    "content_hash": str            # SHA256 for deduplication
}
```

## Key Implementation Details

### Deduplication Logic
The system prevents duplicate articles using:
1. Article ID check (primary key)
2. Content hash check (SHA256 of title + subtitle + content)
3. Automatic skip with detailed reporting in bulk operations

### Scoring Algorithm
```python
# Popularity Score (0-100+)
popularity = reaction_count * 0.3 + wordcount_bonus + time_decay + type_bonus

# Freshness Score (0-100)
freshness = max(0, 100 - days_since_publish * 0.5)

# Quality Score (0-100)
quality = wordcount_score + reaction_score + tag_score

# Combined Score (weighted average)
combined = popularity * 0.4 + freshness * 0.3 + quality * 0.3
```

### Error Handling
- All newsletter operations return success/failure status with messages
- Bulk operations provide detailed skipped/error reports
- Elasticsearch connection failures handled gracefully
- MinIO operations include retry logic

## Integration with Crawler Data

The system is designed to work with output from the Newsletter crawler at `/Users/ruanchuhao/Downloads/Codes/NewsLetters/爬虫mlp`:

1. **Input Format**: `processed_articles.json` from crawler
2. **Preprocessing**: Handles both single articles and arrays
3. **Field Mapping**: Automatic conversion of `postTags` format
4. **Image References**: Preserves local_images metadata

## Performance Considerations

- **Batch Processing**: Default 100 articles per batch
- **Concurrent Uploads**: Async processing for efficiency
- **Index Optimization**: 2 shards, 1 replica for newsletter index
- **Connection Pooling**: Reuses Elasticsearch client connections
- **Memory Management**: Streaming for large file uploads

## Testing Strategy

The codebase includes comprehensive test scripts:
- `test_newsletter_upload.py`: Tests all Newsletter ES features
- `upload_crawled_articles.py`: Production upload with verification
- `test_public_bucket.py`: MinIO bucket operations
- `test_elasticsearch.py`: Basic ES connectivity

Each test includes sample data generation and verification steps.