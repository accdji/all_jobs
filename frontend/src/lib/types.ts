export type OverviewResponse = {
  hero: {
    title: string;
    subtitle: string;
    status: string;
  };
  stats: Array<{
    label: string;
    value: string;
    delta: string;
  }>;
  pipeline: Array<{
    company: string;
    role: string;
    salary: string;
    stage: string;
    summary: string;
    message: string;
  }>;
  threads: Array<{
    company: string;
    time: string;
    incoming: string;
    reply: string;
  }>;
  insight: string;
};

export type ChatResponse = {
  history: Array<{
    title: string;
    preview: string;
    time: string;
    active: boolean;
  }>;
  messages: Array<{
    speaker: "user" | "assistant";
    content: string;
    time: string;
  }>;
  recommendations: Array<{
    title: string;
    company: string;
    tags: string[];
    score: number;
  }>;
  radar: {
    axes: string[];
    score: number;
    tip: string;
  };
};

export type JobsResponse = {
  summary: {
    count: string;
    keyword: string;
  };
  filters: string[];
  jobs: Array<{
    company: string;
    role: string;
    salary: string;
    location: string;
    tags: string[];
    summary: string;
    score: number;
  }>;
  detail: {
    role: string;
    company: string;
    salary: string;
    meta: string[];
    description: string[];
  };
};

export type AiConfigResponse = {
  api_key_configured: boolean;
  api_key_masked: string;
  api_key_env: string;
  provider: string;
  providers: Array<{
    label: string;
    value: string;
    default_base_url: string;
    default_model: string;
  }>;
  base_url: string;
  model: string;
  available_models: Array<{
    label: string;
    value: string;
  }>;
  profile: {
    desired_salary_min: string;
    desired_salary_max: string;
    preferred_location: string;
    skills: string[];
    summary: string;
  };
  subscriptions: Array<{
    key: string;
    label: string;
    description: string;
    channel: string;
    connected: boolean;
  }>;
  knowledge_files: Array<{
    id: string;
    title: string;
    kind: string;
    tags: string[];
  }>;
  storage_used_label: string;
  storage_limit_label: string;
  encryption_enabled: boolean;
  models: Array<{
    name: string;
    provider: string;
    active: boolean;
  }>;
  toggles: Array<{
    title: string;
    description: string;
    enabled: boolean;
  }>;
  push: Array<{
    label: string;
    enabled: boolean;
  }>;
  status: {
    load: string;
    credits: string;
    window: string;
  };
};

export type AiConfigUpdateRequest = {
  api_key?: string | null;
  provider: string;
  base_url: string;
  model: string;
  profile: {
    desired_salary_min: string;
    desired_salary_max: string;
    preferred_location: string;
    skills: string[];
    summary: string;
  };
  subscriptions: Array<{
    key: string;
    label: string;
    description: string;
    channel: string;
    connected: boolean;
  }>;
};

export type InterviewsResponse = {
  pending_count: number;
  cards: Array<{
    company: string;
    role: string;
    mode: string;
    time: string;
    reason: string;
    excerpt: string;
  }>;
  board: {
    weekly: string;
    match: string;
    resume_progress: string;
    upcoming: Array<{
      date: string;
      title: string;
      time: string;
    }>;
    tip: string;
  };
};

export type ResumeLabResponse = {
  score: number;
  quality: string;
  analysis: string;
  variants: Array<{
    name: string;
    tag: string;
  }>;
  pitches: Array<{
    label: string;
    content: string;
  }>;
  progress: number;
};

export type ChatReplyResponse = {
  user_message: string;
  intent: string;
  retrieved: Array<{
    id: string;
    title: string;
    kind: string;
    score: number;
    excerpt: string;
    tags: string[];
  }>;
  draft_reply: string;
  suggested_action: "send_now" | "review_then_send" | "clarify";
  confidence: number;
  provider: string;
  model: string;
};
