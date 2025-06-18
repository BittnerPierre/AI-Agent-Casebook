# AI Developer Collaboration Guidelines

**For all AI coding agents (Claude, Codex, Cursor, etc.) working on this project**

## 🎯 **Core Principle**
AI developers must follow the same professional standards as human developers. No exceptions, no shortcuts.

## 📋 **Mandatory Development Process**

### **Every Feature/Fix Must Include:**

1. **Implementation** ✅
2. **Unit Tests** ✅ 
3. **Integration Testing** ✅
4. **Backward Compatibility** ✅
5. **Documentation** ✅

### **Testing Standards (NON-NEGOTIABLE)**

#### **Before Creating Any PR:**
```bash
# 1. Unit Tests
poetry run pytest examples/genai_training_transcript/tests/ -v

# 2. Integration Test - App Must Still Run
cd src && poetry run python run.py --config ../config.yaml

# 3. Import Validation
poetry run python -c "from existing_modules import *; print('✅ No breaking changes')"

# 4. Existing Functionality Check
# Test that critical workflows still work
```

#### **Common AI Developer Failures to Avoid:**
- ❌ **"Unit tests pass, ship it"** - Integration testing is mandatory
- ❌ **"It works in isolation"** - Must work in full application context  
- ❌ **"Just implementing the feature"** - Quality is holistic responsibility
- ❌ **"Assuming imports work"** - Verify all dependencies explicitly
- ❌ **"Quick and dirty"** - Professional standards apply to AI code

## 🚨 **Quality Gates**

### **Pull Request Requirements:**
- [ ] Feature implemented and working
- [ ] Comprehensive unit test coverage
- [ ] Integration test passing (app runs successfully)
- [ ] No breaking changes to existing functionality
- [ ] Import dependencies verified
- [ ] Documentation updated if needed

### **Code Review Checklist:**
- [ ] Does the application still start and run?
- [ ] Are existing workflows unaffected?
- [ ] Do all tests pass (unit + integration)?
- [ ] Are imports and dependencies correct?
- [ ] Is error handling appropriate?
- [ ] Is the code maintainable and well-documented?

## 🔄 **AI Developer Accountability**

### **Behavioral Standards:**
- **Think like a senior developer** - Consider system-wide impact
- **Test rigorously** - Multiple levels of validation
- **No tunnel vision** - Feature completeness includes quality
- **Professional discipline** - Follow established processes
- **Team responsibility** - Your code affects everyone

### **Common Human Developer Anti-Patterns (AI Must Avoid):**
- Skipping integration tests "because unit tests pass"
- Making assumptions about existing code behavior
- Focusing on feature completion over system stability
- "It works on my machine" mentality
- Rushing to delivery without proper validation

## 🎯 **Project-Specific Standards**

### **This Codebase:**
- **Legacy compatibility** - Training manager and transcript generator must continue working
- **MCP protocol** - New integrations should follow MCP patterns
- **Agent SDK** - Multi-agent coordination via Agent SDK (not LangGraph)
- **Testing pyramid** - Unit → Integration → End-to-end validation

### **Architecture Principles:**
- **KISS** - Keep implementations simple for Sprint 1
- **YAGNI** - Build what's needed, not what might be needed
- **Clean separation** - MCP boundaries between domains
- **Backward compatibility** - Existing workflows must continue working

## 📞 **Escalation Process**

### **When Standards Are Violated:**
1. **Immediate** - Block PR until standards met
2. **Review** - Understand why standards were skipped
3. **Improve** - Update guidelines based on failure patterns
4. **Learn** - Apply lessons to future development

### **No Exceptions Policy:**
- Testing standards are non-negotiable
- Quality is everyone's responsibility
- Professional development practices apply to all contributors
- AI developers are held to the same standards as humans

---

**Remember: You're not just implementing features - you're maintaining a production system that others depend on. Act accordingly.**

🤖 This document applies to all AI coding agents collaborating on this project.

