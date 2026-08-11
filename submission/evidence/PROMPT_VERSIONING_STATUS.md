# Prompt versioning status

The application implements the required prompt contract and trace metadata: `prompt_name`, `prompt_label`, `prompt_version`, and `prompt_source` are sent to both the trace and generation. The automated test for this linkage passes.

No Langfuse public/secret key was available in the provided environment, and `/health` correctly reported `tracing_enabled: false`. Therefore the runtime used the explicit local fallback (`day13-chat`, `production`, `local-v1`) and this repository does **not** claim fabricated managed-prompt v1/v2 or rollback evidence.

To complete the external Langfuse evidence when group credentials are available, follow [docs/PROMPT_VERSIONING.md](../../docs/PROMPT_VERSIONING.md): create v1 (baseline/production), create v2 (candidate), run one request per label, promote `production` to v2, then roll it back to v1 and capture two trace IDs and label history. The code will report the real managed version rather than `local-v1` as soon as the keys and prompt exist.
