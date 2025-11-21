# Provider Architecture

## Overview

The provider layer abstracts embedding generation, allowing easy switching between Google, OpenAI, Cohere, or custom models.

## Provider Interface

```python
class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers"""

    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """Generate single embedding"""
        pass

    @abstractmethod
    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate multiple embeddings"""
        pass

    @abstractmethod
    def health_check(self) -> ProviderHealthResponse:
        """Check provider availability"""
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Embedding dimensions"""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier"""
        pass
```

## Current Implementation: Google

### Google Provider Structure

```
providers/google/
├── provider.py              # GoogleEmbeddingProvider class
├── client.py                # HTTP client with connection pooling
├── request_builder.py       # API request construction
├── response_parser.py       # API response parsing
├── retry_handler.py         # Exponential backoff retry logic
└── batch_processor.py       # Concurrent batch processing
```

### Google API Details

| Aspect | Details |
|--------|---------|
| **Endpoint** | `generativelanguage.googleapis.com/v1beta` |
| **Model** | `text-embedding-004` |
| **Dimensions** | 768 |
| **Max text length** | ~10,000 tokens |
| **Rate limit** | Varies by API key tier |
| **Cost** | ~$0.00001 per embedding |

### Request Format

```json
{
  "content": "Fix authentication bug",
  "model": "models/text-embedding-004",
  "taskType": "SEMANTIC_SIMILARITY",
  "outputDimensionality": 768
}
```

### Response Format

```json
{
  "embedding": {
    "values": [0.123, -0.456, ..., 0.789]
  }
}
```

### Retry Logic

```python
def generate_with_retry(text: str) -> List[float]:
    for attempt in range(3):
        try:
            return make_api_call(text)
        except RateLimitError:
            if attempt == 2:
                raise
            wait = 2 ** attempt  # 1s, 2s, 4s
            sleep(wait)
        except ServerError:
            if attempt == 2:
                raise
            sleep(1)
```

## Adding New Providers

### Example: OpenAI Provider

```python
class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self._model = "text-embedding-3-small"
        self._dimensions = 1536

    def generate_embedding(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            input=text,
            model=self._model
        )
        return response.data[0].embedding

    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            input=texts,
            model=self._model
        )
        return [item.embedding for item in response.data]

    def health_check(self) -> ProviderHealthResponse:
        try:
            self.generate_embedding("test")
            return ProviderHealthResponse(
                healthy=True,
                provider="openai",
                latency_ms=100
            )
        except Exception as e:
            return ProviderHealthResponse(
                healthy=False,
                provider="openai",
                error=str(e)
            )

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return self._model
```

### Example: Custom Model Provider

```python
class CustomModelProvider(EmbeddingProvider):
    """Use your own local model"""

    def __init__(self, model_path: str):
        import torch
        from transformers import AutoModel, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModel.from_pretrained(model_path)
        self._dimensions = self.model.config.hidden_size

    def generate_embedding(self, text: str) -> List[float]:
        # Tokenize
        tokens = self.tokenizer(text, return_tensors="pt")

        # Generate embedding
        with torch.no_grad():
            output = self.model(**tokens)

        # Use CLS token or mean pooling
        embedding = output.last_hidden_state[:, 0, :].squeeze()

        return embedding.tolist()

    # ... implement other methods
```

## Provider Comparison

| Provider | Model | Dimensions | Cost (per 1M) | Speed | Quality |
|----------|-------|------------|---------------|-------|---------|
| **Google** | text-embedding-004 | 768 | $10 | Fast | Excellent |
| **OpenAI** | text-embedding-3-small | 1536 | $20 | Fast | Excellent |
| **OpenAI** | text-embedding-3-large | 3072 | $130 | Medium | Best |
| **Cohere** | embed-english-v3.0 | 1024 | $10 | Fast | Excellent |
| **Custom** | sentence-transformers | 384-1024 | Free | Varies | Good |

## Provider Selection Strategy

### When to Use Google (Current)

✅ Good for:
- Cost-effective production use
- 768 dimensions sufficient
- Fast response times needed
- Standard semantic similarity

### When to Consider OpenAI

Consider if:
- Need higher dimensions (1536/3072)
- Already using OpenAI ecosystem
- Budget allows higher cost
- Need best possible quality

### When to Consider Custom Model

Consider if:
- Have specific domain (medical, legal, etc.)
- Need complete data privacy
- Want to avoid API costs
- Have infrastructure for inference

## Configuration

### Environment Variables

```bash
# Provider selection
EMBEDDING_PROVIDER=google  # google | openai | cohere | custom

# Google
GOOGLE_API_KEY=your_key_here

# OpenAI
OPENAI_API_KEY=your_key_here

# Custom
CUSTOM_MODEL_PATH=/path/to/model
```

### Provider Factory

```python
def create_provider(config: ProviderConfig) -> EmbeddingProvider:
    if config.provider_type == "google":
        return GoogleEmbeddingProvider(
            api_key=config.api_key,
            model=config.model
        )
    elif config.provider_type == "openai":
        return OpenAIEmbeddingProvider(
            api_key=config.api_key
        )
    elif config.provider_type == "custom":
        return CustomModelProvider(
            model_path=config.model_path
        )
    else:
        raise ValueError(f"Unknown provider: {config.provider_type}")
```

## Migration Between Providers

### Considerations

When switching providers:

1. **Dimension mismatch**: Different models = different dimensions
   - Google: 768 dims
   - OpenAI small: 1536 dims
   - Solution: Re-generate all embeddings

2. **Semantic space mismatch**: Vectors not comparable
   - Can't search Google embeddings with OpenAI query
   - Solution: Full migration, not gradual

3. **Cost implications**: Calculate new costs

### Migration Process

```python
async def migrate_provider(
    old_provider: str,
    new_provider: str
):
    # 1. Switch provider
    embedding_service.set_provider(new_provider)

    # 2. Clear cache (old embeddings incompatible)
    cache.clear()

    # 3. Re-generate all embeddings
    memories = get_all_memories()

    for memory in memories:
        text = extract_searchable_text(memory)
        new_embedding = embedding_service.generate_embedding(text)

        # Update vector database
        vector_repo.update_embedding(
            id=memory.id,
            embedding=new_embedding
        )

        # Update PostgreSQL
        db.update_embedding(memory.id, new_embedding)

    logger.info(f"Migrated {len(memories)} embeddings to {new_provider}")
```

## Best Practices

1. **Abstract away provider**: Application code shouldn't know which provider
2. **Health checks**: Monitor provider availability
3. **Fallback provider**: Have backup for high availability
4. **Cost monitoring**: Track API usage and costs
5. **Test thoroughly**: Validate embedding quality before full migration

---

*Part of the [Embedding Documentation](./README.md)*
