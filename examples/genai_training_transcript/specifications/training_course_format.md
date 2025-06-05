# Training Course Format Specification

This document describes the expected format and structure for training course data in the GenAI Training Transcript Generator project.

## Directory Structure

Training courses are stored in the `data/training_courses/` directory and follow these patterns:

### Single File Courses
```
data/training_courses/
├── Course_Name.txt
├── Another_Course_Name.txt
└── ...
```

### Multi-Module Courses
```
data/training_courses/
└── <course_id> - <course_name>/
    └── transcripts/
        ├── module1_en - <course_name> - 1 - <module_title>.txt
        ├── module2_en - <course_name> - 2 - <module_title>.txt
        └── ...
```

## Naming Conventions

### Course Directory Names
- Pattern: `<course_id> - <course_name>`
- Example: `CHROMA - Chroma Course`
- Spaces around the dash separator are required
- Course ID should be uppercase and descriptive

### Module File Names
- Pattern: `module<N>_en - <course_name> - <N> - <module_title>.txt`
- Example: `module1_en - Chroma - 1 - Introduction.txt`
- `<N>` is the module number (1-based)
- Language code is always `en` for English
- Spaces around dash separators are required

### Single File Course Names
- Pattern: `<Course_Name_With_Underscores>.txt`
- Example: `Advanced_Retrieval_for_AI.txt`
- Use underscores instead of spaces
- Use title case

## File Content Format

### Raw Transcript Files (.txt)
- Plain text format
- Contains raw transcript content from training videos/sessions
- May include timestamps, speaker names, or other metadata
- No specific formatting requirements (preprocessing handles cleanup)

## Output Structure

After processing, the system generates:

```
output/
└── <COURSE_ID>/
    ├── cleaned_transcripts/
    │   ├── module1_en - <course_name> - 1 - <module_title>.md
    │   └── ...
    └── metadata/
        └── index.json
```

### Cleaned Transcripts
- Converted to Markdown format (.md)
- Cleaned and formatted for readability
- Structured with proper headings and sections

### Metadata
- JSON format containing course and module information
- Includes processing timestamps and configuration

## Usage with Training Manager

To process a course, use the course directory path:

```bash
# For multi-module courses
poetry run run_training_manager --course-path "data/training_courses/CHROMA - Chroma Course"

# For single file courses (specify the file directly)
poetry run run_training_manager --course-path "data/training_courses/Course_Name.txt"
```

## Course Path Guidelines

1. **Always use quotes** around paths containing spaces
2. **Use the exact directory name** as it appears in the filesystem
3. **Include the full relative path** from the project root
4. **Maintain case sensitivity** for course IDs and names

## Adding New Courses

1. Create appropriate directory structure in `data/training_courses/`
2. Follow naming conventions exactly
3. Place raw transcript files in the correct location
4. Test processing with the training manager
5. Verify output in the `output/` directory

## File Safety

- Original `.txt` files are never modified or deleted
- All processing creates new files in the `output/` directory
- Use `--overwrite` flag to regenerate existing output files