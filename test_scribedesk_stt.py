#!/usr/bin/env python3
"""Tests for readable API error messages in scribedesk_stt.py.

Must not import the `elevenlabs` package — scribedesk_stt.py only imports
it inside main(), so these tests build fake exception objects that mimic
the shape of elevenlabs.core.api_error.ApiError instead.
"""

import contextlib
import io
import json
import os
import tempfile
import unittest
import wave

import scribedesk_stt


HEADERS = {
    'date': 'Sun, 23 Aug 2026 15:04:50 GMT',
    'server': 'uvicorn',
    'content-length': '167',
    'content-type': 'application/json',
    'vary': 'Accept-Language',
    'access-control-allow-origin': '*',
    'access-control-allow-headers': '*',
    'access-control-allow-methods': 'POST, PATCH, OPTIONS, DELETE, GET, PUT',
    'access-control-max-age': '600',
    'strict-transport-security': 'max-age=1800;',
    'x-trace-id': '79012d1a8a0393272cabb483dee87b3f',
    'x-region': 'us-central1',
    'via': '1.1 google',
    'alt-svc': 'h3=":443"; ma=2592000',
}


class FakeApiError(Exception):
    def __init__(self, status_code=None, body=None, headers=None):
        self.status_code = status_code
        self.body = body
        self.headers = headers

    def __str__(self):
        return f"headers: {self.headers}, status_code: {self.status_code}, body: {self.body}"


class HostileBody:
    """A body whose .get raises — simulates an exotic SDK object."""

    def get(self, *args, **kwargs):
        raise RuntimeError("nope")


class TestDescribeApiError(unittest.TestCase):
    def test_auth_error_is_readable(self):
        exc = FakeApiError(
            status_code=401,
            headers=HEADERS,
            body={
                'detail': {
                    'type': 'authentication_error',
                    'code': 'unauthorized',
                    'message': 'Invalid API key',
                    'status': 'invalid_api_key',
                    'request_id': 'abc',
                }
            },
        )
        result = scribedesk_stt.describe_api_error(exc)
        self.assertIn("HTTP 401", result)
        self.assertIn("Invalid API key", result)
        self.assertIn("ELEVENLABS_API_KEY", result)
        self.assertNotIn("headers:", result)
        self.assertNotIn("uvicorn", result)
        self.assertNotIn("alt-svc", result)

    def test_validation_error_names_the_field(self):
        exc = FakeApiError(
            status_code=422,
            headers=HEADERS,
            body={
                'detail': [
                    {
                        'type': 'less_than_equal',
                        'loc': ['body', 'num_speakers'],
                        'msg': 'Input should be less than or equal to 32',
                        'input': '99',
                        'ctx': {'le': 32},
                    }
                ]
            },
        )
        result = scribedesk_stt.describe_api_error(exc)
        self.assertIn("num_speakers", result)
        self.assertIn("Input should be less than or equal to 32", result)
        self.assertNotIn("uvicorn", result)
        self.assertNotIn("alt-svc", result)
        self.assertNotIn("'ctx'", result)

    def test_multiple_validation_errors_are_joined(self):
        exc = FakeApiError(
            status_code=422,
            headers=HEADERS,
            body={
                'detail': [
                    {
                        'type': 'less_than_equal',
                        'loc': ['body', 'num_speakers'],
                        'msg': 'Input should be less than or equal to 32',
                    },
                    {
                        'type': 'value_error',
                        'loc': ['body', 'temperature'],
                        'msg': 'Input should be less than or equal to 2.0',
                    },
                ]
            },
        )
        result = scribedesk_stt.describe_api_error(exc)
        self.assertIn("num_speakers", result)
        self.assertIn("temperature", result)
        idx1 = result.index("num_speakers")
        idx2 = result.index("temperature")
        between = result[min(idx1, idx2):max(idx1, idx2)]
        self.assertIn("; ", between)

    def test_body_as_json_string_is_parsed(self):
        body_dict = {
            'detail': {
                'type': 'authentication_error',
                'code': 'unauthorized',
                'message': 'Invalid API key',
                'status': 'invalid_api_key',
                'request_id': 'abc',
            }
        }
        exc = FakeApiError(status_code=401, headers=HEADERS, body=json.dumps(body_dict))
        result = scribedesk_stt.describe_api_error(exc)
        self.assertIn("Invalid API key", result)
        self.assertNotIn('{"detail"', result)

    def test_out_of_credits_hint(self):
        exc = FakeApiError(status_code=402, headers=HEADERS, body={'message': 'Insufficient credits'})
        result = scribedesk_stt.describe_api_error(exc)
        self.assertIn("out of credits", result)

    def test_plain_exception_falls_back(self):
        result = scribedesk_stt.describe_api_error(ValueError("connection reset"))
        self.assertIn("connection reset", result)

    def test_never_raises_on_hostile_body(self):
        exc1 = FakeApiError(status_code=500, headers=HEADERS, body=HostileBody())
        result1 = scribedesk_stt.describe_api_error(exc1)
        self.assertIsInstance(result1, str)

        exc2 = FakeApiError(status_code=500, headers=HEADERS, body="not json at all {{{")
        result2 = scribedesk_stt.describe_api_error(exc2)
        self.assertIsInstance(result2, str)

    def test_result_is_one_line_and_bounded(self):
        long_msg = ("line one\nline two\n" * 500)[:5000]
        exc = FakeApiError(status_code=422, headers=HEADERS, body={'detail': {'message': long_msg}})
        result = scribedesk_stt.describe_api_error(exc)
        self.assertNotIn("\n", result)
        self.assertLessEqual(len(result), 400)

    def test_process_file_prints_the_readable_line(self):
        exc = FakeApiError(
            status_code=401,
            headers=HEADERS,
            body={
                'detail': {
                    'type': 'authentication_error',
                    'code': 'unauthorized',
                    'message': 'Invalid API key',
                    'status': 'invalid_api_key',
                    'request_id': 'abc',
                }
            },
        )

        class StubSTT:
            def convert(self, **kwargs):
                raise exc

        class StubClient:
            def __init__(self):
                self.speech_to_text = StubSTT()

        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        try:
            with wave.open(path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b"\x00\x00" * 16000)

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                result = scribedesk_stt.process_file(
                    StubClient(), path,
                    out_format="text",
                    output_path=None,
                    speakers=False,
                    language=None,
                    num_speakers=None,
                    tag_audio_events=True,
                    timestamps_granularity="word",
                    diarization_threshold=None,
                    no_verbatim=False,
                    detect_speaker_roles=False,
                    keyterms=None,
                    temperature=None,
                    seed=None,
                    label_map=None,
                    inline_timestamps=False,
                    no_print=True,
                )
            output = buf.getvalue()
            self.assertIn("⚠  Transcription failed:", output)
            self.assertIn("HTTP 401", output)
            self.assertIn("Invalid API key", output)
            self.assertNotIn("alt-svc", output)
            self.assertNotIn("uvicorn", output)
            self.assertFalse(result)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
