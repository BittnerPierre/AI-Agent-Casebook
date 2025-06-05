from tools.file_client_loader import load_transcripts


def test_load_transcripts(tmp_path):
    # Create sample directory structure with .txt files
    data_dir = tmp_path / "training_courses"
    transcripts_dir = data_dir / "Course1" / "transcripts"
    transcripts_dir.mkdir(parents=True)
    file1 = transcripts_dir / "mod1.txt"
    file1.write_text("test content", encoding="utf-8")

    config = {"raw_transcripts_dir": str(data_dir)}
    transcripts = load_transcripts(config)
    # Expect module ID 'mod1' with content
    assert "mod1" in transcripts
    assert transcripts["mod1"] == "test content"