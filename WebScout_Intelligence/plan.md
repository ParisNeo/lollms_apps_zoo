# Web Knowledge Extractor and Organizer

## Requirements
- Web scraping of multiple URLs with configurable depth
- Text extraction from HTML elements (h, p, span)
- Text tokenization and chunking
- LLM-based subject extraction and information organization
- Persistent storage of intermediate results
- Step-by-step processing with recovery capability

## Libraries to Use
- Axios/Fetch for web requests
- Cheerio for HTML parsing
- GPT-Tokenizer for text tokenization
- LocalStorage for data persistence
- Lollms generateCode method for LLM processing

## User Interface Elements
### Input Section
- URL input field with add button
- URL list display with remove option
- Depth selector (1-5)
- Chunk size input (default: 4096)
- Start Scraping button

### Progress Section
- Step indicator
- Progress bars for each step
- Status messages
- Pause/Resume buttons
- Save/Load state buttons

### Results Section
- Subjects list view
- Information preview panel
- Export options
- Rewrite trigger button

## Processing Steps
1. **URL Collection**
   - Input validation
   - URL list management
   - Configuration settings

2. **Web Scraping**
   - Depth-first crawling
   - Text extraction
   - Raw text storage

3. **Text Processing**
   - Tokenization
   - Chunk creation
   - Chunk storage

4. **Subject Extraction**
   - LLM processing
   - JSON structure maintenance
   - Subject list updates

5. **Information Organization**
   - JSON data aggregation
   - Subject-info mapping
   - Content concatenation

6. **Content Refinement**
   - Final LLM processing
   - Format enhancement
   - Result presentation

## Data Structures
```javascript
// Persistent State
{
    urls: string[],
    depth: number,
    chunkSize: number,
    rawText: string,
    chunks: string[],
    subjects: string[],
    processedData: {
        [subject: string]: string
    },
    currentStep: number,
    processedChunks: number
}

// LLM Output Format
{
    subjects: string[],
    extracted_infos: {
        [subject: string]: string
    }
}
```

## Error Handling
- Network error recovery
- LLM processing retry
- State corruption protection
- Progress auto-save
- Manual checkpoint system

## File Structure
```
index.html
|- <style> CSS section
|- <script> JavaScript section
   |- Constants
   |- State Management
   |- UI Controllers
   |- Processing Functions
   |- Error Handlers
   |- Main Application
```