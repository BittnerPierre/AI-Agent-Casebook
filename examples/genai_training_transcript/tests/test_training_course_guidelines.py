import os
import sys
import subprocess


def test_guidelines_file_exists():
    """
    Ensure the training course narrative guidelines file is present.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    guidelines_path = os.path.join(
        base_dir,
        'src',
        'transcript_generator',
        'guidelines',
        'training_course_guidelines.md',
    )
    assert os.path.isfile(guidelines_path), f"Guidelines file not found: {guidelines_path}"


def test_guidelines_content():
    """
    Validate key sections exist in the guidelines file.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    guidelines_path = os.path.join(
        base_dir,
        'src',
        'transcript_generator',
        'guidelines',
        'training_course_guidelines.md',
    )
    content = open(guidelines_path, encoding='utf-8').read()
    assert '## Pedagogical Patterns' in content, 'Pedagogical Patterns section missing'
    assert '### 1. Learning Scaffolding' in content, 'Learning Scaffolding subsection missing'
    assert '### Prompt: Course Structure Outline' in content, 'Prompt template missing'


def test_run_help_exit_zero_and_description():
    """
    Basic integration: verify the CLI help runs without errors and shows description.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    run_path = os.path.join(base_dir, 'src', 'run.py')
    result = subprocess.run(
        [sys.executable, run_path, '--help'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert result.returncode == 0, f"CLI help failed: {result.stdout}"
    assert 'Run GenAI Training Transcript Generator' in result.stdout, 'CLI help description missing'