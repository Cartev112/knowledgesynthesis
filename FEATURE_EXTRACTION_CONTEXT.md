# Feature: Extraction Context

## Overview
Added "Extraction Context" feature to guide AI extraction based on user interests. Replaced the manual "Document Title" field (now auto-extracted) with a natural language context field.

## Changes Made

### 1. Frontend (main_ui.py)

**Removed:**
- "Document Title" input field

**Added:**
- "Extraction Context" textarea with placeholder examples
- Help text: "Guide the AI: describe what types of relationships you're most interested in"

**Updated JavaScript:**
- Changed `doc-title` → `extraction-context`
- Changed `title` → `extractionContext`
- Sends `extraction_context` parameter to backend

### 2. Backend - Ingest Route (ingest.py)

**Updated `/pdf` endpoint:**
- Removed `title: Optional[str] = Form(None)` parameter
- Added `extraction_context: Optional[str] = Form(None)` parameter
- Removed conditional title logic (always auto-extracts now)
- Passes `extraction_context` to `extract_triplets()`

**Logging:**
```python
if extraction_context:
    logger.info(f"Using extraction context: {extraction_context[:100]}...")
```

### 3. Backend - OpenAI Extraction (openai_extract.py)

**Updated `extract_triplets()` signature:**
```python
def extract_triplets(
    text: str, 
    max_triplets: int = 50, 
    pages: list = None, 
    extraction_context: str = None
) -> TripletExtractionResult:
```

**Prompt Enhancement:**
When `extraction_context` is provided, prepends to system prompt:
```
=== USER'S EXTRACTION FOCUS ===
{user's context}
=== END FOCUS ===

Please prioritize extracting relationships that align with the user's stated interests above. 
However, still extract other significant relationships found in the text.
```

## Usage Examples

### Example 1: Protein Research
```
I'm interested in proteins and their functional relationships, 
especially binding interactions and enzymatic activities.
```

### Example 2: Drug Discovery
```
Focus on drug-target interactions, mechanism of action, 
and clinical efficacy data.
```

### Example 3: Disease Mechanisms
```
Extract relationships related to disease pathways, 
genetic mutations, and therapeutic targets.
```

### Example 4: Neuroscience
```
I'm studying neural circuits and synaptic connections. 
Focus on neurotransmitters, receptors, and signaling pathways.
```

## Benefits

1. **Guided Extraction**: AI focuses on user-relevant relationships
2. **Flexible**: Still extracts other significant relationships
3. **Simple UX**: Natural language, no complex configuration
4. **Backward Compatible**: Optional field, works without context
5. **Auto Titles**: No manual title entry needed (auto-extracted from document)

## Technical Details

- **Field**: Optional textarea, sent as `extraction_context` form parameter
- **Prompt Position**: Prepended to system prompt before main instructions
- **Logging**: Context logged (first 100 chars) for debugging
- **Validation**: No validation required, empty string is fine

## Testing

1. Upload PDF without context → Works as before
2. Upload PDF with context "proteins and binding" → Should extract more protein-related relationships
3. Upload PDF with context "clinical trials" → Should prioritize clinical data
4. Multiple files with same context → Context applied to all

## Future Enhancements

- Save user's preferred contexts
- Suggest contexts based on document content
- Show which relationships matched the context
- Context templates for common research areas




