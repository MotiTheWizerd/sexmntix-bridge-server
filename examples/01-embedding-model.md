# Embedding Model and API

## Overview
Semantix-Brain uses **Google's text-embedding-004 model** to generate vector embeddings from text.

## Model Details

**Model:** `models/text-embedding-004`
**API Endpoint:** `https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent`
**Output:** Vector of floating-point numbers representing semantic meaning

## Implementation

### File Location
`semantix-brain/src/infrastructure/embeddings/embedding_service.py`

### Key Class: `EmbeddingService`

```python
class EmbeddingService:
    async def generate_embedding(text: str) -> list[float]
```

### How It Works

1. **HTTP Client Setup**
   - Uses `httpx.AsyncClient` for async requests
   - 30-second timeout
   - API key from environment variable

2. **Request Format**
   ```python
   {
       "model": "models/text-embedding-004",
       "content": {
           "parts": [{"text": input_text}]
       }
   }
   ```

3. **Response Format**
   ```python
   {
       "embedding": {
           "values": [0.123, -0.456, 0.789, ...]  # Vector
       }
   }
   ```

4. **Error Handling**
   - Custom `EmbeddingGenerationError` exception
   - Handles HTTP errors, timeouts, JSON parsing issues

## Configuration

### Environment Variable
```bash
GOOGLE_API_KEY=your_api_key_here
```

### Settings File
`semantix-brain/src/infrastructure/config/settings.py`

```python
class Settings(BaseSettings):
    google_api_key: str
```

## API Key Setup

1. Get API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Add to `.env` file in semantix-brain root
3. Service auto-loads from environment

## Cost Considerations

- Google charges per 1,000 characters
- Embeddings are cached in ChromaDB
- No re-embedding needed once stored
- Migration scripts handle batch processing efficiently

## Why Google's text-embedding-004?

- High-quality semantic understanding
- Fast response times
- Cost-effective for development use
- Good performance on technical/code-related text
- Native async support
