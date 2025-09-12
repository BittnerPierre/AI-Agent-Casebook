# August 2025 Release Notes
## GPT-5 Integration & Technical Infrastructure Cleanup

### 🚀 Overview
**Single major commit** on August 26th, 2025 (`c31d5e7` - PR #135): GPT-5 integration with codebase standardization and critical bug fixes.

---

## 🤖 GPT-5 Integration

### New Models Added (`app/core/base.py`)
- `GPT_5_MINI` - Primary GPT-5 model
- `MISTRAL_MEDIUM` - Additional Mistral variant  
- `CLAUDE_SONNET_4_O` - Claude 4.0
- Renamed: `CLAUDE_SONNET` → `CLAUDE_SONNET_3_7`, `CLAUDE_HAIKU` → `CLAUDE_HAIKU_3_5`

### Model-Specific Configuration Files
- `config-gpt-5-min.ini` - GPT-5 settings
- `config-gpt-4o-mini.ini` - GPT-4o Mini settings
- `config_mistral-small.ini` - Mistral Small settings

### VideoScript Model Configuration ⭐ **NEW FEATURE**
**Before**: Models hardcoded in code  
**After**: Configurable via config files

```ini
[VideoScript]
planner_model = gpt-5-mini    # Agents SDK format
worker_model = GPT_5_MINI     # Enum format  
producer_model = GPT_5_MINI
```

**Impact**: Easy model comparison without code changes (Issue #142 tracks making this runtime configurable)

---

## 🔧 Critical Technical Fixes

### LangGraph Compatibility Issue
**Problem**: LangGraph now blocks sync calls within async functions  
**Impact**: GPT-5 and Agents SDK make internal sync calls  
**Solution**: **Must use `--allow-blocking` flag**

```bash
# Required command:
poetry run langgraph dev --allow-blocking
```

### Corrective RAG Fixes
- **Fixed import**: `TavilySearchResults` → `TavilySearch`
- **Fixed import paths**: Added `app.` prefixes throughout `app/crag/agents.py`
- **Configuration-driven model**: Uses config instead of hardcoded default

### Planner-Evaluator Fixes
- **Finalized implementation**: Fixed vague/incorrect prompts that were causing failures
- **Already used Agents SDK**: Prompts were the issue, not the architecture
- **Issue #136**: Suggested search support still to be implemented

### LangSmith API Updates
Updated sync LangSmith API calls to async patterns for LangGraph compatibility

---

## 🏗️ Infrastructure Cleanup

### Import Path Standardization
**Major change**: Added `app.` prefixes across entire codebase
- 25+ application files updated
- 15+ test files updated
- All relative imports converted to absolute imports

### Test Infrastructure  
- **pytest configuration**: Added proper pythonpath, testpaths, filterwarnings
- **Agent initialization**: All agents now require `name` parameter
- **LangGraph compatibility**: Removed deprecated `AddableValuesDict` usage

### Performance Optimizations
**VideoScript settings** (`app/video_script/configuration.py`):
- `max_search_results`: 10 → 3
- `max_revision`: 2 → 1

---

## 📦 Dependencies

### Major Updates
- **openai-agents**: `>=0.0.14` → `^0.2.9` (with litellm extras)
- **Python**: `>=3.12,<4.0` → `>=3.12,<=3.13`

### New Dependencies
- `langchain-voyageai ^0.1.7` - Voyage embeddings (ready, not activated)
- `langchain-tavily ^0.2.11` - Tavily search for CRAG
- `langgraph-api ^0.2.137`

---

## 📋 Issue Status

### ✅ Resolved
- **#127**: GPT-5 model integration
- **#137**: CRAG import fixes (partial - config foundation added)

### 🟡 Partially Fixed
- **#136**: Planner-Evaluator prompts fixed, suggested search support still pending

### ❌ Still Open  
- **#134**: Customer onboarding function calling with GPT-5 - **NOT FIXED**
- **#138**: Application failure on plan rejection - **NOT FIXED**
- **#142**: Runtime model configuration for VideoScript - **NEW ISSUE**

---

## ⚠️ Breaking Changes

### Required Operational Change
```bash
# Old (no longer works):
poetry run langgraph dev

# New (required):
poetry run langgraph dev --allow-blocking
```

### Import Updates
All imports now use `app.` prefixes (already fixed in codebase)

### Agent Initialization
```python
# Old:
agent = EligibilityAgent(model=model)

# New:
agent = EligibilityAgent(name="EligibilityAgent", model=model)
```

---

## 🎯 Key Achievement

**Configurable VideoScript Models**: Can now compare GPT-5, GPT-4o, Claude 4.0, and Mistral performance on identical workflows via config files instead of code changes.

**Next**: Issue #142 tracks making model selection runtime configurable rather than requiring server restart.

---

**Developer**: Pierre Bittner <pierre@bittner.fr>  
**AI Collaboration**: 🤖 Generated with [Claude Code](https://claude.ai/code)