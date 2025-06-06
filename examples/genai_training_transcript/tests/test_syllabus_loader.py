from transcript_generator.tools.syllabus_loader import load_syllabus


def test_load_syllabus(tmp_path):
    content = """# Sample Syllabus

## Course Objective

### Module 1: Foo
* Objective A
* Objective B

### Module 2: Bar
* Objective C
""".strip()
    syllabus_file = tmp_path / "syllabus.md"
    syllabus_file.write_text(content, encoding="utf-8")
    modules = load_syllabus(str(syllabus_file))
    assert isinstance(modules, list)
    assert modules[0]["title"] == "Foo"
    assert modules[0]["objectives"] == ["Objective A", "Objective B"]
    assert modules[1]["title"] == "Bar"
    assert modules[1]["objectives"] == ["Objective C"]