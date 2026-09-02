PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS sources (
  source_id INTEGER PRIMARY KEY AUTOINCREMENT,
  repo_owner TEXT NOT NULL,
  repo_name TEXT NOT NULL,
  github_url TEXT NOT NULL,
  file_path TEXT,
  license_spdx TEXT,
  usage_class TEXT NOT NULL CHECK(usage_class IN ('COMMERCIAL_OK','TRANSFORM_ONLY','RESEARCH_ONLY','BLOCKED','UNKNOWN')),
  attribution_required INTEGER DEFAULT 0,
  share_alike INTEGER DEFAULT 0,
  noncommercial_only INTEGER DEFAULT 0,
  stars INTEGER,
  last_commit TEXT,
  retrieved_at TEXT,
  source_commit_sha TEXT,
  sha256 TEXT,
  UNIQUE(repo_owner, repo_name, file_path, source_commit_sha)
);

CREATE TABLE IF NOT EXISTS viral_hooks (
  hook_id INTEGER PRIMARY KEY AUTOINCREMENT,
  hook_category TEXT, hook_formula TEXT NOT NULL, psychology_trigger TEXT,
  opening_style TEXT, platform TEXT, recommended_duration INTEGER,
  product_category TEXT, audience_type TEXT, tone TEXT,
  example_original TEXT, example_normalized TEXT,
  commercial_safe INTEGER DEFAULT 0, claim_risk TEXT DEFAULT 'LOW',
  formula_family TEXT, quality_score REAL DEFAULT 0,
  source_id INTEGER, FOREIGN KEY(source_id) REFERENCES sources(source_id)
);

CREATE TABLE IF NOT EXISTS short_form_scripts (
  script_id INTEGER PRIMARY KEY AUTOINCREMENT,
  framework_name TEXT NOT NULL, platform TEXT, duration_sec INTEGER,
  hook_phase TEXT, context_phase TEXT, value_phase TEXT, proof_phase TEXT,
  payoff_phase TEXT, cta_phase TEXT, spoken_template TEXT, onscreen_template TEXT,
  visual_template TEXT, shot_pattern TEXT, loop_strategy TEXT,
  product_category TEXT, tone TEXT, quality_score REAL DEFAULT 0,
  source_id INTEGER, FOREIGN KEY(source_id) REFERENCES sources(source_id)
);

CREATE TABLE IF NOT EXISTS ctas (
  cta_id INTEGER PRIMARY KEY AUTOINCREMENT,
  cta_type TEXT, goal TEXT, cta_template TEXT NOT NULL, strength TEXT,
  platform TEXT, funnel_stage TEXT, product_category TEXT, tone TEXT,
  urgency_level INTEGER DEFAULT 0, engagement_risk TEXT DEFAULT 'LOW',
  quality_score REAL DEFAULT 0, source_id INTEGER,
  FOREIGN KEY(source_id) REFERENCES sources(source_id)
);

CREATE TABLE IF NOT EXISTS before_after_patterns (
  before_after_id INTEGER PRIMARY KEY AUTOINCREMENT,
  problem_state TEXT, transition_pattern TEXT, product_entry TEXT,
  proof_pattern TEXT, after_state TEXT, spoken_template TEXT,
  visual_pattern TEXT, onscreen_template TEXT, duration_sec INTEGER,
  product_category TEXT, claim_risk TEXT DEFAULT 'LOW',
  quality_score REAL DEFAULT 0, source_id INTEGER,
  FOREIGN KEY(source_id) REFERENCES sources(source_id)
);

CREATE TABLE IF NOT EXISTS product_demo_patterns (
  demo_id INTEGER PRIMARY KEY AUTOINCREMENT,
  demo_type TEXT, opening_pattern TEXT, product_action TEXT,
  feature_focus TEXT, proof_method TEXT, camera_pattern TEXT,
  spoken_template TEXT, onscreen_template TEXT, cta_type TEXT,
  duration_sec INTEGER, product_category TEXT,
  quality_score REAL DEFAULT 0, source_id INTEGER,
  FOREIGN KEY(source_id) REFERENCES sources(source_id)
);

CREATE TABLE IF NOT EXISTS testimonial_patterns (
  testimonial_id INTEGER PRIMARY KEY AUTOINCREMENT,
  testimonial_type TEXT, problem TEXT, discovery TEXT, experience TEXT,
  usage TEXT, result TEXT, recommendation TEXT, proof_level TEXT,
  spoken_template TEXT, visual_pattern TEXT, duration_sec INTEGER,
  product_category TEXT, claim_risk TEXT DEFAULT 'LOW',
  quality_score REAL DEFAULT 0, source_id INTEGER,
  FOREIGN KEY(source_id) REFERENCES sources(source_id)
);

CREATE INDEX IF NOT EXISTS idx_hooks_family ON viral_hooks(formula_family);
CREATE INDEX IF NOT EXISTS idx_hooks_category ON viral_hooks(hook_category);
CREATE INDEX IF NOT EXISTS idx_scripts_framework ON short_form_scripts(framework_name);
CREATE INDEX IF NOT EXISTS idx_sources_usage ON sources(usage_class);
