from io import BytesIO
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import UploadFile

from ai_agent.ui.backend import router
from ai_agent.ui.backend.service import AiAgentService


@pytest.mark.asyncio
async def test_transcribe_audio_bytes_returns_validated_text():
    with patch.object(
        AiAgentService,
        "_call_groq_audio_transcription",
        new=AsyncMock(return_value="show all leedz"),
    ), patch.object(
        AiAgentService,
        "_validate_transcript_with_cerebras",
        new=AsyncMock(return_value={"text": "show all leads", "validator": "cerebras", "changed": True}),
    ), patch("ai_agent.ui.backend.service.GROQ_API_KEY", "groq-test-key"):
        response = await AiAgentService.transcribe_audio_bytes(
            file_bytes=b"voice-bytes",
            filename="voice.webm",
            content_type="audio/webm",
            language_preference="eng",
        )

    assert response["status"] == "ok"
    assert response["text"] == "show all leads"
    assert response["raw_text"] == "show all leedz"
    assert response["provider"] == "groq"
    assert response["validator"] == "cerebras"


@pytest.mark.asyncio
async def test_transcribe_audio_bytes_rejects_unsupported_audio_type():
    response = await AiAgentService.transcribe_audio_bytes(
        file_bytes=b"voice-bytes",
        filename="voice.txt",
        content_type="text/plain",
        language_preference="eng",
    )

    assert response["status"] == "error"
    assert "Unsupported audio format" in response["text"]


@pytest.mark.asyncio
async def test_transcribe_audio_bytes_accepts_webm_codec_content_type():
    with patch.object(
        AiAgentService,
        "_call_groq_audio_transcription",
        new=AsyncMock(return_value="show all leads"),
    ), patch.object(
        AiAgentService,
        "_validate_transcript_with_cerebras",
        new=AsyncMock(return_value={"text": "show all leads", "validator": "cerebras", "changed": False}),
    ), patch("ai_agent.ui.backend.service.GROQ_API_KEY", "groq-test-key"):
        response = await AiAgentService.transcribe_audio_bytes(
            file_bytes=b"voice-bytes",
            filename="voice.webm",
            content_type="audio/webm;codecs=opus",
            language_preference="eng",
        )

    assert response["status"] == "ok"
    assert response["text"] == "show all leads"


@pytest.mark.asyncio
async def test_stt_router_reads_uploaded_file_and_delegates_to_service():
    upload = UploadFile(filename="voice.webm", file=BytesIO(b"voice-bytes"))
    upload.headers = {"content-type": "audio/webm"}

    with patch.object(
        AiAgentService,
        "transcribe_audio_bytes",
        new=AsyncMock(
            return_value={
                "status": "ok",
                "text": "show all leads",
                "raw_text": "show all leads",
                "provider": "groq",
                "validator": "cerebras",
            }
        ),
    ) as transcribe_call:
        response = await router.transcribe_audio(
            audio=upload,
            conversation_id="phase273-stt",
            language_preference="eng",
        )

    assert response["status"] == "ok"
    assert response["text"] == "show all leads"
    transcribe_call.assert_awaited_once()
