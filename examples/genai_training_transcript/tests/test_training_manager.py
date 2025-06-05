#!/usr/bin/env python3
"""
Unit tests for transcript preprocessor and metadata extractor.
"""

import pytest

from transcript_generator.tools.transcript_preprocessor import preprocess_transcript, Runner as PreprocessorRunner
from transcript_generator.tools.metadata_extractor import extract_metadata, Runner as MetadataRunner


class DummyOutput:
    def __init__(self, content=None, summary=None, keywords=None, tags=None):
        self.content = content
        self.summary = summary
        self.keywords = keywords
        self.tags = tags


class DummyResult:
    def __init__(self, output: DummyOutput):
        self.final_output = output

    def final_output_as(self, model):
        return model(
            summary=self.final_output.summary,
            keywords=self.final_output.keywords,
            tags=self.final_output.tags,
        )


async def dummy_preprocess(*args, **kwargs):
    return DummyResult(DummyOutput(content="cleaned content"))


async def dummy_metadata(*args, **kwargs):
    return DummyResult(
        DummyOutput(summary="summary text", keywords=["kw1", "kw2"], tags=["tag"])
    )


@pytest.mark.asyncio
async def test_preprocess_transcript(monkeypatch):
    monkeypatch.setattr(PreprocessorRunner, "run", dummy_preprocess)
    cleaned = await preprocess_transcript("mod1.txt", None)
    assert cleaned == "cleaned content"


@pytest.mark.asyncio
async def test_extract_metadata(monkeypatch):
    monkeypatch.setattr(MetadataRunner, "run", dummy_metadata)
    meta = await extract_metadata("mod1.txt", "cleaned content")
    assert meta.summary == "summary text"
    assert meta.keywords == ["kw1", "kw2"]
    assert meta.tags == ["tag"]