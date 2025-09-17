# Claude Development Assistant Configuration

## Project Context
This is a university website crawler designed for business intelligence. The system uses a pipeline architecture to extract metrics, contacts, and content from university websites for sales team analysis.

## Development Guidelines

### Code Standards
- Use Python 3.9+ with type hints
- Follow PEP 8 style guidelines  
- Prefer composition over inheritance
- Write docstrings for all public functions
- Use dataclasses/pydantic for data models
- Adhere to DRY principles
- Use modern Pyhton best practices

### Architecture Principles
- **Pipeline-based**: Each stage processes items individually
- **Recovery-first**: Always implement checkpointing
- **Fail-fast**: Detect issues early, fail gracefully
- **Configurable**: Use config.py for all settings
- **Modular**: Keep stages independent and testable

### Testing Strategy
- Unit tests for individual pipeline stages
- Integration tests for full pipeline flow
- Mock external HTTP requests in tests
- Test recovery scenarios explicitly

### Key Commands
- **Install dependencies**: `pip install -r requirements.txt`
- **Run crawler**: `python main.py domain university.edu`
- **Resume job**: `python main.py resume job_id`
- **Export to CSV**: `python main.py export job_id --csv`
- **Export to JSON**: `python main.py export job_id --json`
- **Generate BI reports**: `python main.py get-report job_id`
- **Lint code**: `ruff check .`
- **Type check**: `mypy .`

## Implementation Notes

### Pipeline Stages
Each stage should:
- Accept items from previous stage
- Process item independently
- Update checkpoint state
- Handle errors gracefully
- Pass results to next stage

### Error Handling Strategy
- Network errors: Retry with exponential backoff
- Rate limiting: Adaptive delay adjustment
- Content extraction failures: Fallback to simpler methods
- Blocking detection: Log reason and adjust strategy

### Recovery System
- Save pipeline state after each processed item
- Store failed URLs with error details and retry strategies
- Enable resuming from any pipeline stage
- Maintain separate queues for pending/processing/completed URLs

### Data Priorities
1. **Metrics**: Page counts, subdomains, link analysis (highest priority)
2. **Contacts**: Email extraction, social media handles (medium priority)  
3. **Content**: Clean markdown conversion (lowest priority)

## Development Workflow

### Phase 1: Core Pipeline
1. Create project structure and basic models
2. Implement URL discovery and fetching stages
3. Add checkpointing system
4. Build basic content extraction

### Phase 2: Intelligence
1. Add adaptive rate limiting
2. Implement blocking detection
3. Create contact extraction
4. Build CSV export system

### Phase 3: Enhancement  
1. Add Crawl4AI integration
2. Implement advanced analytics
3. Create multiple export formats
4. Add dashboard capabilities

## Common Issues & Solutions

### University Protection
- **Issue**: Rate limiting or IP blocking
- **Solution**: Implement adaptive delays and graceful degradation

### JavaScript-heavy Sites
- **Issue**: Empty content from BeautifulSoup
- **Solution**: Fallback to Crawl4AI for browser-based extraction

### Large Sites
- **Issue**: Memory usage or processing time
- **Solution**: Implement streaming processing and pagination

### Recovery Failures
- **Issue**: Corrupted checkpoint state
- **Solution**: Validate checkpoint integrity on resume

Remember: This is a business intelligence tool, not a web scraping framework. Focus on data quality and reliable extraction over raw crawling speed.