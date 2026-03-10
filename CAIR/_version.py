__version__ = "0.10.0"

"""
Version 0.10.0: Add a YouTube Data API helper to resolve channel IDs from @handle URLs with cache coverage and tests.
Version 0.9.0: Add stop_before support for Channel.get_uploads, including date-based early pagination cutoff and cache-key separation for filtered upload queries.
Version 0.8.3: Remove extra S3 PCM buffer copy by constructing numpy audio directly from bytearray output.
Version 0.8.2: Add richer transcription logging for S3 numpy load boundaries, model load completion/status, and transcription start timing after model readiness.
Version 0.8.1: Fix VAD handling for transcribe_s3 with independent VAD cache keying, numpy-audio VAD support, and writable tensor conversion; sync packaging/demo updates.
Version 0.8.0: Add faster_whisper transcription method, optional Silero VAD computation/caching, VAD overlap flagging, and transcription progress output support.
Version 0.7.0: Add Granicus metadata properties, ViewPublisher discovery helper, and HTML upload parsing with tests.
Version 0.6.3: Add S3 streaming transcription helper, expose S3 utility, and add tests/README updates.
Version 0.6.2: Add optional `websearch` flag to Analyze/chat_with_openai to enable OpenAI `web_search` tool per request.
Version 0.6.1: Add optional `js_runtimes` support for yt-dlp audio downloads in `Video.download_audio`.
Version 0.6.0: Move YouTube metadata/search/upload caching to runtime-configurable TTL per Search/Video/Channel instance.
Version 0.5.2: Allow `model_name` in CallParameters by disabling Pydantic protected `model_` namespace for that model.
Version 0.5.1: Add force and cache_result options to control cache reads/writes.
Version 0.5.0: Breaking change, invalidates cache. Now start logging usage.
Version 0.4.1: Include service_tier in cache key to respect tier overrides.
Version 0.4.0: Added OpenAI request timeout and service_tier options; exposed on Analyze.
Version 0.3.0: Packaging and API fixes; restored Analyze helpers; lazy API clients.
Version 0.2.5: Add specific call option for Analyze
Version 0.2.4: Add package prompt data
Version 0.2.3: Added cache_expiration to chat_with_ai
Version 0.2.2: Added seed option in chat_with_ai
Version 0.2.1: Added some more channel options.
Version 0.2.0: Updating many backend components for use on a real civic project.
Version 0.1.0: First release. Basic downloading, transcription, and analysis.
"""
