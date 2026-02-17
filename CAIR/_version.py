__version__ = "0.6.1"

"""
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
