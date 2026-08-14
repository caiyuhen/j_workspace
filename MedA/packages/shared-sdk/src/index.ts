export type { CreateProjectRequest, ProjectResponse } from "./client";

export {
  DEMO_PRESETS,
  DEMO_PRESET_BY_KEY,
  type DemoPreset,
  type DemoPresetKey,
} from "./presets";
export {
  build_grouped_terms_from_pico,
  build_expression_from_boolean_text,
  ensureDemoProjectAndQuery,
  type EnsureDemoResult,
  type EnsureDemoOptions,
} from "./utils/demoSeedings";
