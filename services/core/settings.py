from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MAD_",
        extra="ignore",
        populate_by_name=True,
    )

    env: str = "development"
    host: str = "127.0.0.1"
    port: int = 8000
    text_demo_mode: bool = False
    data_dir: Path = Path("data")
    sqlite_path: Path = Path("data/mad.sqlite3")
    workspace_root: Path = Path(".")
    virtual_devices_path: Path = Path("data/virtual_devices.json")
    presence_path: Path = Path("data/presence.json")
    voice_profile_path: Path = Path("data/voice_profile.json")
    voice_identity_path: Path = Path("data/mad_voice.json")
    voice_state_path: Path = Path("data/voice_state.json")
    audio_output_dir: Path = Path("data/audio")
    vision_observations_path: Path = Path("data/vision_observations.json")
    camera_snapshot_dir: Path = Path("data/camera_snapshots")
    vision_semantic_enabled: bool = False
    vision_semantic_base_url: str = "http://127.0.0.1:11434/v1"
    vision_semantic_model: str = "qwen2.5vl:3b"
    vision_semantic_api_key: str = ""
    vision_semantic_timeout_seconds: float = 180.0
    live_vision_enabled: bool = True
    visual_observation_max_age_seconds: int = 600
    visual_object_min_confidence: float = 0.55
    spatial_memory_min_confidence: float = 0.70
    live_task_completion_confidence: float = 0.82
    live_task_confirmation_observations: int = 2
    live_guidance_cooldown_seconds: int = 15
    live_guidance_max_per_minute: int = 2
    study_retention_half_life_days: float = 30.0
    study_mastery_threshold: float = 0.70
    study_probability_min_scored_sessions: int = 2
    study_probability_max_margin: float = 0.20
    curiosity_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("AGENT_CURIOSITY_ENABLED", "MAD_CURIOSITY_ENABLED"),
    )
    curiosity_max_minutes_per_day: float = Field(
        default=15.0,
        validation_alias=AliasChoices(
            "AGENT_CURIOSITY_MAX_MINUTES_PER_DAY",
            "MAD_CURIOSITY_MAX_MINUTES_PER_DAY",
        ),
    )
    curiosity_max_cpu_percent: float = Field(
        default=35.0,
        validation_alias=AliasChoices(
            "AGENT_CURIOSITY_MAX_CPU_PERCENT",
            "MAD_CURIOSITY_MAX_CPU_PERCENT",
        ),
    )
    curiosity_max_network_mb: float = Field(
        default=25.0,
        validation_alias=AliasChoices(
            "AGENT_CURIOSITY_MAX_NETWORK_MB",
            "MAD_CURIOSITY_MAX_NETWORK_MB",
        ),
    )
    curiosity_idle_seconds: int = 300
    curiosity_tick_seconds: int = Field(
        default=60,
        validation_alias=AliasChoices(
            "MAD_CURIOSITY_TICK_SECONDS",
            "MAD_CURIOSITY_POLL_SECONDS",
        ),
    )
    curiosity_job_timeout_seconds: float = 120.0
    curiosity_max_sources: int = 3
    face_profiles_path: Path = Path("data/face_profiles.json")
    face_identity_enabled: bool = False
    face_match_tolerance: float = 0.5
    authorized_visual_contexts: str = "private_home,user_device,enrollment"

    assistant_name: str = Field(
        default="Maddy",
        validation_alias=AliasChoices("AGENT_NAME", "MAD_ASSISTANT_NAME"),
    )
    user_name: str = "Usuario"
    local_computer_name: str = "LocalComputer"
    msi_name: str = "SecondaryHost"
    homelab_name: str = "Homelab"
    timezone: str = "Europe/Madrid"
    wake_phrase: str = "maddy"
    user_country_code: str = "ES"
    confirmation_ttl_seconds: int = 300
    online_learning_enabled: bool = True
    model_weight_updates_enabled: bool = False
    learning_contact_url: str = ""
    learning_wikimedia_projects: str = "es.wikibooks.org,es.wikipedia.org"
    learning_stackexchange_enabled: bool = True
    learning_max_sources: int = 6
    learning_timeout_seconds: float = 15.0
    learning_max_source_bytes: int = 1_000_000
    learning_excerpt_chars: int = 6000
    learning_working_chars: int = 12000
    video_learning_enabled: bool = True
    pattern_intelligence_enabled: bool = True
    pattern_shadow_mode: bool = True
    pattern_min_evidence: int = 5
    pattern_min_distinct_days: int = 3
    pattern_confidence_threshold: float = 0.72
    pattern_half_life_days: float = 30.0
    pattern_cooldown_minutes: int = 1440
    pattern_budget_per_hour: int = 1
    pattern_budget_per_day: int = 3
    pattern_min_gap_minutes: int = 30
    device_fabric_enabled: bool = True
    workspace_allowed_roots: str = ""
    workspace_readiness_timeout_seconds: float = 30.0
    mission_max_parallel_steps: int = 4
    mission_step_timeout_seconds: float = 120.0
    mission_rollback_on_failure: bool = True

    stt_provider: str = "hybrid"
    whisper_model: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_language: str = "es"
    whisper_beam_size: int = 1
    whisper_vad_silence_ms: int = 420
    whisper_hotwords: str = (
        "MAD, Home Assistant, LG, YouTube, Netflix, PlayStation, MSI, Homelab"
    )
    stt_warmup_enabled: bool = True
    speaker_identification_on_every_request: bool = False
    vosk_model_path: Path = Path("data/models/vosk-model-small-es-0.42")
    speaker_model_path: Path = Path("data/models/vosk-model-spk-0.4")
    speaker_match_threshold: float = 0.72
    stt_fast_confidence: float = 0.78

    tts_provider: str = "edge"
    kokoro_model_path: Path = Path("models/kokoro/kokoro-v1.0.onnx")
    kokoro_voices_path: Path = Path("models/kokoro/voices-v1.0.bin")
    kokoro_voice: str = "ef_dora"
    kokoro_threads: int = Field(default=4, ge=1, le=8)
    multilingual_voice: str = "en-US-AvaMultilingualNeural"
    azure_speech_key: str = ""
    azure_speech_region: str = ""
    edge_tts_rate: str = "+0%"
    edge_tts_volume: str = "+0%"
    edge_tts_pitch: str = "+0Hz"
    tts_warmup_enabled: bool = True
    tts_first_audio_timeout_seconds: float = Field(default=20.0, gt=0, le=120)
    voice_dedupe_window_ms: int = 1800
    voice_metrics_retention: int = 200
    voice_realtime_enabled: bool = True
    voice_stream_verify_whisper: bool = True
    voice_stream_sample_rate: int = 16000
    voice_stream_vad_start_rms: float = 0.018
    voice_stream_vad_end_rms: float = 0.010
    voice_stream_vad_start_ms: float = 80.0
    voice_stream_endpoint_ms: float = 420.0
    voice_stream_min_speech_ms: float = 180.0
    voice_stream_max_utterance_ms: float = 15000.0
    voice_stream_preroll_ms: float = 240.0
    primary_audio_output: str = "default"
    audio_reconnect_command: str = ""

    llm_provider: str = "stub"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-5.5"
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:8b"
    llama_cpp_base_url: str = "http://127.0.0.1:11435/v1"
    llama_cpp_model: str = "qwen3:1.7b"
    llm_timeout_seconds: float = 180.0
    llm_warmup_enabled: bool = True
    runtime_warmup_delay_seconds: float = 2.0
    llm_history_limit: int = Field(default=8, ge=1, le=32)
    llm_temperature: float = 0.6
    llm_max_output_tokens: int = 160
    llm_detailed_output_tokens: int = Field(default=640, ge=160, le=4096)

    home_assistant_url: str = ""
    home_assistant_token: str = ""
    home_assistant_domains: str = (
        "light,switch,fan,climate,media_player,cover,input_boolean,scene,script"
    )
    home_assistant_verify_ssl: bool = True
    weather_entity_id: str = ""
    temperature_entity_id: str = ""
    weather_location_name: str = ""
    weather_latitude: float | None = None
    weather_longitude: float | None = None
    weather_max_age_minutes: int = 90
    dashboard_cache_seconds: int = 20

    person_entity_id: str = ""
    phone_tracker_entity_id: str = ""
    phone_battery_entity_id: str = ""
    phone_charging_entity_id: str = ""
    mobile_notify_service: str = ""
    ps4_entity_id: str = ""
    perception_poll_seconds: int = 30
    companion_online_seconds: int = 180
    event_cooldown_seconds: int = 900
    proactive_notifications_enabled: bool = True
    proactive_speech_enabled: bool = True
    camera_perception_enabled: bool = True
    lenovo_camera_index: int = 0
    lenovo_camera_location_id: str = ""
    lenovo_camera_location_label: str = ""
    wellbeing_enabled: bool = True
    security_guardian_enabled: bool = True
    personal_safety_enabled: bool = True
    personal_safety_correlation_seconds: int = 90
    personal_safety_signal_max_age_seconds: int = 180
    personal_safety_history_limit: int = 200
    calling_enabled: bool = False
    call_provider: str = "twilio"
    call_recipient: str = ""
    call_public_base_url: str = ""
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    presence_enabled: bool = True
    health_poll_seconds: int = 60
    security_scan_seconds: int = 300
    wellbeing_cooldown_seconds: int = 7200
    phone_battery_notice_level: int = 20
    phone_battery_important_level: int = 10
    phone_battery_critical_level: int = 5
    vehicle_enabled: bool = True
    vehicle_provider: str = "disabled"
    embodiment_enabled: bool = True
    ar_renderer: str = "web_manifest"
    gaze_enabled: bool = True
    gaze_provider: str = "disabled"
    future_glasses_enabled: bool = True
    future_glasses_provider: str = "disabled"
    digital_twin_provider: str = "disabled"
    maddy_room_enabled: bool = True
    maddy_room_renderer: str = "three_webgl"

    msi_host: str = ""
    msi_mac: str = ""
    msi_broadcast: str = ""
    msi_wol_port: int = 9
    msi_check_port: int = 22
    msi_wake_on_morning_greeting: bool = True
    msi_offline_confirmation_attempts: int = 3
    msi_offline_confirmation_interval_seconds: float = 0.4
    msi_wake_timeout_seconds: float = 45.0
    msi_wake_poll_seconds: float = 2.0
    msi_ssh_user: str = ""
    msi_ssh_private_key: str = ""
    msi_remote_documents_path: str = ""
    msi_code_workspace: str = ""
    msi_code_execution_enabled: bool = False
    msi_ssh_timeout_seconds: float = 90.0

    tv_entity_id: str = ""
    tv_host: str = ""
    tv_mac: str = ""
    tv_broadcast: str = ""
    tv_wol_port: int = 9
    tv_wake_timeout_seconds: float = 30.0
    tv_game_source: str = "HDMI1"
    tv_movie_source: str = "Netflix"
    tv_game_volume: int = 18
    tv_movie_volume: int = 22

    mqtt_host: str = ""
    mqtt_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""

    mobile_webhook_url: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_to: str = ""
    smtp_starttls: bool = True
    whatsapp_recipient: str = ""
    daily_briefing_enabled: bool = True
    daily_briefing_hour: int = 8
    daily_briefing_minute: int = 0
    arrival_scene_entity_id: str = ""
    departure_scene_entity_id: str = ""
    calendar_ics_url: str = ""
    calendar_ics_path: str = ""
    agent_command_execution_enabled: bool = False
    agent_command_mode: str = "confirm"
    agent_command_deny_patterns: str = (
        "format ,diskpart,remove-item -recurse,rm -rf,shutdown /s,del /s,reg delete"
    )
    allowed_commands: dict[str, str] = Field(default_factory=dict)
    recovery_commands: dict[str, str] = Field(default_factory=dict)
    security_commands: dict[str, str] = Field(default_factory=dict)
    recovery_max_attempts: int = 2
    recovery_cooldown_seconds: int = 900
    recovery_verify_seconds: float = 12.0

    @field_validator("allowed_commands", "recovery_commands", "security_commands", mode="before")
    @classmethod
    def parse_allowed_commands(cls, value: Any) -> dict[str, str]:
        if isinstance(value, dict):
            return value
        if not value:
            return {}
        if isinstance(value, str):
            parsed = json.loads(value)
            if not isinstance(parsed, dict):
                raise TypeError("command settings must be a JSON object")
            return {str(key): str(command) for key, command in parsed.items()}
        raise TypeError("command settings must be a dictionary")

    @field_validator(
        "weather_latitude",
        "weather_longitude",
        mode="before",
    )
    @classmethod
    def parse_optional_number(cls, value: Any) -> Any:
        if value == "":
            return None
        return value

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.virtual_devices_path.parent.mkdir(parents=True, exist_ok=True)
        self.presence_path.parent.mkdir(parents=True, exist_ok=True)
        self.voice_profile_path.parent.mkdir(parents=True, exist_ok=True)
        self.voice_identity_path.parent.mkdir(parents=True, exist_ok=True)
        self.voice_state_path.parent.mkdir(parents=True, exist_ok=True)
        self.audio_output_dir.mkdir(parents=True, exist_ok=True)
        self.vision_observations_path.parent.mkdir(parents=True, exist_ok=True)
        self.camera_snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.face_profiles_path.parent.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "curiosity_lab").mkdir(parents=True, exist_ok=True)
