/**
 * GitHub Webhook Types
 * エス・エー・エス株式会社 GitHub Webhook セキュリティシステム
 */

// Base Types
export interface GitHubRepository {
  id: number;
  name: string;
  full_name: string;
  private: boolean;
  html_url: string;
  description?: string;
  default_branch: string;
  owner: GitHubUser;
  clone_url: string;
  ssh_url: string;
  size: number;
  stargazers_count: number;
  watchers_count: number;
  language?: string;
  has_issues: boolean;
  has_projects: boolean;
  has_wiki: boolean;
  has_pages: boolean;
  archived: boolean;
  disabled: boolean;
  visibility: 'public' | 'private' | 'internal';
  created_at: string;
  updated_at: string;
  pushed_at: string;
}

export interface GitHubUser {
  id: number;
  login: string;
  avatar_url: string;
  html_url: string;
  type: 'User' | 'Bot' | 'Organization';
  site_admin: boolean;
  name?: string;
  email?: string;
  bio?: string;
  company?: string;
  location?: string;
  blog?: string;
  twitter_username?: string;
  public_repos?: number;
  public_gists?: number;
  followers?: number;
  following?: number;
  created_at?: string;
  updated_at?: string;
}

export interface GitHubCommit {
  id: string;
  tree_id: string;
  distinct: boolean;
  message: string;
  timestamp: string;
  url: string;
  author: GitHubCommitAuthor;
  committer: GitHubCommitAuthor;
  added: string[];
  removed: string[];
  modified: string[];
}

export interface GitHubCommitAuthor {
  name: string;
  email: string;
  username?: string;
}

export interface GitHubPullRequest {
  id: number;
  number: number;
  state: 'open' | 'closed';
  locked: boolean;
  title: string;
  body?: string;
  created_at: string;
  updated_at: string;
  closed_at?: string;
  merged_at?: string;
  merge_commit_sha?: string;
  assignee?: GitHubUser;
  assignees: GitHubUser[];
  requested_reviewers: GitHubUser[];
  requested_teams: GitHubTeam[];
  labels: GitHubLabel[];
  milestone?: GitHubMilestone;
  draft: boolean;
  commits_url: string;
  review_comments_url: string;
  review_comment_url: string;
  comments_url: string;
  statuses_url: string;
  html_url: string;
  diff_url: string;
  patch_url: string;
  issue_url: string;
  user: GitHubUser;
  head: GitHubPullRequestBranch;
  base: GitHubPullRequestBranch;
  merged: boolean;
  mergeable?: boolean;
  rebaseable?: boolean;
  mergeable_state: string;
  merged_by?: GitHubUser;
  comments: number;
  review_comments: number;
  maintainer_can_modify: boolean;
  commits: number;
  additions: number;
  deletions: number;
  changed_files: number;
}

export interface GitHubPullRequestBranch {
  label: string;
  ref: string;
  sha: string;
  user: GitHubUser;
  repo: GitHubRepository;
}

export interface GitHubLabel {
  id: number;
  url: string;
  name: string;
  color: string;
  default: boolean;
  description?: string;
}

export interface GitHubMilestone {
  id: number;
  number: number;
  title: string;
  description?: string;
  creator: GitHubUser;
  open_issues: number;
  closed_issues: number;
  state: 'open' | 'closed';
  created_at: string;
  updated_at: string;
  due_on?: string;
  closed_at?: string;
}

export interface GitHubTeam {
  id: number;
  name: string;
  slug: string;
  description?: string;
  privacy: 'closed' | 'secret';
  permission: 'pull' | 'push' | 'admin' | 'maintain' | 'triage';
  url: string;
  html_url: string;
  members_url: string;
  repositories_url: string;
  parent?: GitHubTeam;
}

export interface GitHubIssue {
  id: number;
  number: number;
  title: string;
  body?: string;
  user: GitHubUser;
  labels: GitHubLabel[];
  state: 'open' | 'closed';
  locked: boolean;
  assignee?: GitHubUser;
  assignees: GitHubUser[];
  milestone?: GitHubMilestone;
  comments: number;
  created_at: string;
  updated_at: string;
  closed_at?: string;
  author_association: string;
  active_lock_reason?: string;
  draft?: boolean;
  pull_request?: {
    url: string;
    html_url: string;
    diff_url: string;
    patch_url: string;
  };
  html_url: string;
  repository_url: string;
  labels_url: string;
  comments_url: string;
  events_url: string;
}

// Webhook Event Payloads
export interface BasePushPayload {
  ref: string;
  before: string;
  after: string;
  created: boolean;
  deleted: boolean;
  forced: boolean;
  base_ref?: string;
  compare: string;
  commits: GitHubCommit[];
  head_commit?: GitHubCommit;
  repository: GitHubRepository;
  pusher: {
    name: string;
    email: string;
  };
  sender: GitHubUser;
}

export interface PullRequestPayload {
  action: 'assigned' | 'auto_merge_disabled' | 'auto_merge_enabled' | 'closed' | 
          'converted_to_draft' | 'demilestoned' | 'dequeued' | 'edited' | 
          'labeled' | 'locked' | 'milestoned' | 'opened' | 'queued' | 
          'ready_for_review' | 'reopened' | 'review_request_removed' | 
          'review_requested' | 'synchronize' | 'unassigned' | 'unlabeled' | 
          'unlocked';
  number: number;
  pull_request: GitHubPullRequest;
  repository: GitHubRepository;
  sender: GitHubUser;
  changes?: Record<string, unknown>;
  requested_reviewer?: GitHubUser;
  requested_team?: GitHubTeam;
  assignee?: GitHubUser;
  label?: GitHubLabel;
  milestone?: GitHubMilestone;
}

export interface IssuesPayload {
  action: 'assigned' | 'closed' | 'deleted' | 'demilestoned' | 'edited' | 
          'labeled' | 'locked' | 'milestoned' | 'opened' | 'pinned' | 
          'reopened' | 'transferred' | 'unassigned' | 'unlabeled' | 
          'unlocked' | 'unpinned';
  issue: GitHubIssue;
  repository: GitHubRepository;
  sender: GitHubUser;
  changes?: Record<string, unknown>;
  assignee?: GitHubUser;
  label?: GitHubLabel;
  milestone?: GitHubMilestone;
}

export interface RepositoryPayload {
  action: 'archived' | 'created' | 'deleted' | 'edited' | 'privatized' | 
          'publicized' | 'renamed' | 'transferred' | 'unarchived';
  repository: GitHubRepository;
  sender: GitHubUser;
  changes?: Record<string, unknown>;
}

export interface OrganizationPayload {
  action: 'deleted' | 'member_added' | 'member_invited' | 'member_removed' | 'renamed';
  invitation?: {
    id: number;
    login: string;
    email?: string;
    role: string;
    created_at: string;
    inviter: GitHubUser;
    team_count: number;
    invitation_teams_url: string;
  };
  membership?: {
    url: string;
    state: 'active' | 'pending';
    role: 'admin' | 'member' | 'billing_manager';
    organization_url: string;
    user: GitHubUser;
  };
  organization: {
    login: string;
    id: number;
    url: string;
    repos_url: string;
    events_url: string;
    hooks_url: string;
    issues_url: string;
    members_url: string;
    public_members_url: string;
    avatar_url: string;
    description?: string;
    gravatar_id?: string;
    name?: string;
    company?: string;
    blog?: string;
    location?: string;
    email?: string;
    twitter_username?: string;
    is_verified: boolean;
    has_organization_projects: boolean;
    has_repository_projects: boolean;
    public_repos: number;
    public_gists: number;
    followers: number;
    following: number;
    html_url: string;
    created_at: string;
    updated_at: string;
    type: 'Organization';
    total_private_repos?: number;
    owned_private_repos?: number;
    private_gists?: number;
    disk_usage?: number;
    collaborators?: number;
    billing_email?: string;
    plan?: {
      name: string;
      space: number;
      private_repos: number;
      collaborators: number;
    };
    default_repository_permission?: 'read' | 'write' | 'admin' | 'none';
    members_can_create_repositories?: boolean;
    two_factor_requirement_enabled?: boolean;
    members_allowed_repository_creation_type?: string;
    members_can_create_public_repositories?: boolean;
    members_can_create_private_repositories?: boolean;
    members_can_create_internal_repositories?: boolean;
    members_can_create_pages?: boolean;
    members_can_fork_private_repositories?: boolean;
    web_commit_signoff_required?: boolean;
    advanced_security_enabled_for_new_repositories?: boolean;
    dependency_graph_enabled_for_new_repositories?: boolean;
    dependency_graph_enabled_for_new_repositories_default?: boolean;
    dependabot_alerts_enabled_for_new_repositories?: boolean;
    dependabot_security_updates_enabled_for_new_repositories?: boolean;
    dependabot_security_updates_enabled_for_new_repositories_default?: boolean;
  };
  sender: GitHubUser;
}

export interface MemberPayload {
  action: 'added' | 'edited' | 'removed';
  member: GitHubUser;
  repository: GitHubRepository;
  sender: GitHubUser;
  changes?: {
    permission?: {
      from: string;
    };
  };
}

export interface TeamPayload {
  action: 'added_to_repository' | 'created' | 'deleted' | 'edited' | 
          'removed_from_repository';
  team: GitHubTeam;
  repository?: GitHubRepository;
  organization: OrganizationPayload['organization'];
  sender: GitHubUser;
  changes?: Record<string, unknown>;
}

export interface InstallationPayload {
  action: 'created' | 'deleted' | 'suspend' | 'unsuspend' | 'new_permissions_accepted';
  installation: {
    id: number;
    account: GitHubUser;
    repository_selection: 'all' | 'selected';
    access_tokens_url: string;
    repositories_url: string;
    html_url: string;
    app_id: number;
    target_id: number;
    target_type: 'Organization' | 'User';
    permissions: Record<string, string>;
    events: string[];
    created_at: string;
    updated_at: string;
    single_file_name?: string;
    has_multiple_single_files?: boolean;
    single_file_paths?: string[];
    app_slug: string;
    suspended_by?: GitHubUser;
    suspended_at?: string;
  };
  repositories?: Array<{
    id: number;
    name: string;
    full_name: string;
    private: boolean;
  }>;
  sender: GitHubUser;
}

// Security Alert Payloads
export interface SecretScanningAlertPayload {
  action: 'created' | 'reopened' | 'resolved' | 'revoked';
  alert: {
    number: number;
    secret_type: string;
    secret_type_display_name: string;
    secret: string;
    repository: GitHubRepository;
    push_protection_bypassed?: boolean;
    push_protection_bypassed_by?: GitHubUser;
    push_protection_bypassed_at?: string;
    resolution?: 'false_positive' | 'wont_fix' | 'revoked' | 'used_in_tests' | null;
    resolved_by?: GitHubUser;
    resolved_at?: string;
    resolution_comment?: string;
    html_url: string;
    locations_url: string;
    created_at: string;
    updated_at: string;
  };
  repository: GitHubRepository;
  organization?: OrganizationPayload['organization'];
  sender: GitHubUser;
}

export interface CodeScanningAlertPayload {
  action: 'appeared_in_branch' | 'closed_by_user' | 'created' | 'fixed' | 'reopened' | 'reopened_by_user';
  alert: {
    number: number;
    created_at: string;
    updated_at: string;
    url: string;
    html_url: string;
    state: 'open' | 'dismissed' | 'fixed';
    fixed_at?: string;
    dismissed_by?: GitHubUser;
    dismissed_at?: string;
    dismissed_reason?: 'false positive' | 'used in tests' | 'wont fix' | null;
    dismissed_comment?: string;
    rule: {
      id: string;
      severity: 'error' | 'warning' | 'note';
      description: string;
      name?: string;
      full_description?: string;
      tags?: string[];
      help?: string;
      help_uri?: string;
    };
    tool: {
      name: string;
      guid?: string;
      version?: string;
    };
    most_recent_instance: {
      ref: string;
      analysis_key: string;
      category?: string;
      environment?: string;
      location: {
        path: string;
        start_line: number;
        end_line: number;
        start_column: number;
        end_column: number;
      };
      message: {
        text: string;
      };
      classifications?: string[];
    };
    instances_url: string;
  };
  ref: string;
  commit_oid: string;
  repository: GitHubRepository;
  organization?: OrganizationPayload['organization'];
  sender: GitHubUser;
}

export interface DependabotAlertPayload {
  action: 'created' | 'dismissed' | 'fixed' | 'reintroduced' | 'reopened';
  alert: {
    number: number;
    state: 'auto_dismissed' | 'dismissed' | 'fixed' | 'open';
    dependency: {
      package: {
        ecosystem: string;
        name: string;
      };
      manifest_path?: string;
      scope?: 'development' | 'runtime';
    };
    security_advisory: {
      ghsa_id: string;
      cve_id?: string;
      summary: string;
      description: string;
      vulnerabilities: Array<{
        package: {
          ecosystem: string;
          name: string;
        };
        severity: 'low' | 'moderate' | 'high' | 'critical';
        vulnerable_version_range: string;
        first_patched_version?: {
          identifier: string;
        };
      }>;
      severity: 'low' | 'moderate' | 'high' | 'critical';
      cvss: {
        vector_string?: string;
        score?: number;
      };
      cwes: Array<{
        cwe_id: string;
        name: string;
      }>;
      identifiers: Array<{
        value: string;
        type: string;
      }>;
      references: Array<{
        url: string;
      }>;
      published_at: string;
      updated_at: string;
      withdrawn_at?: string;
    };
    security_vulnerability: {
      package: {
        ecosystem: string;
        name: string;
      };
      severity: 'low' | 'moderate' | 'high' | 'critical';
      vulnerable_version_range: string;
      first_patched_version?: {
        identifier: string;
      };
    };
    url: string;
    html_url: string;
    created_at: string;
    updated_at: string;
    dismissed_at?: string;
    dismissed_by?: GitHubUser;
    dismissed_reason?: 'fix_started' | 'inaccurate' | 'no_bandwidth' | 'not_used' | 'tolerable_risk';
    dismissed_comment?: string;
    fixed_at?: string;
  };
  repository: GitHubRepository;
  organization?: OrganizationPayload['organization'];
  sender: GitHubUser;
}

// Union type for all webhook payloads
export type WebhookPayload = 
  | BasePushPayload
  | PullRequestPayload
  | IssuesPayload
  | RepositoryPayload
  | OrganizationPayload
  | MemberPayload
  | TeamPayload
  | InstallationPayload
  | SecretScanningAlertPayload
  | CodeScanningAlertPayload
  | DependabotAlertPayload;

// Webhook Event Types
export type WebhookEventType = 
  | 'push'
  | 'pull_request'
  | 'issues'
  | 'repository'
  | 'organization'
  | 'member'
  | 'team'
  | 'installation'
  | 'secret_scanning_alert'
  | 'code_scanning_alert'
  | 'dependabot_alert';

// Request/Response Types
export interface WebhookHeaders {
  'x-github-delivery': string;
  'x-github-event': WebhookEventType;
  'x-github-hook-id'?: string;
  'x-github-hook-installation-target-id'?: string;
  'x-hub-signature-256': string;
  'user-agent': string;
  'content-type': 'application/json';
  'content-length': string;
}

export interface WebhookRequest {
  headers: WebhookHeaders;
  body: WebhookPayload;
  rawBody: Buffer;
  ip: string;
}

export interface WebhookResponse {
  status: 'success' | 'error';
  delivery_id: string;
  event_type?: WebhookEventType;
  processing_time_ms?: number;
  timestamp: string;
  metadata?: {
    repository?: string;
    sender?: string;
    action?: string;
    commits_processed?: number;
    security_checks_passed?: boolean;
    sensitive_data_detected?: boolean;
  };
  error?: string;
  message?: string;
  details?: string;
  request_id?: string;
  validation_errors?: Array<{
    field: string;
    message: string;
    value?: unknown;
  }>;
}

// Configuration Types
export interface WebhookSecurityConfig {
  webhook_secret: string;
  allowed_ips: string[];
  rate_limits: {
    global_per_minute: number;
    per_ip_per_minute: number;
    per_hook_per_minute: number;
    per_repository_per_minute: number;
    burst_capacity: number;
  };
  max_payload_size_bytes: number;
  signature_algorithm: 'sha256';
  ip_validation_strict: boolean;
  geo_restrictions: string[];
  custom_allowlist: string[];
}

export interface ServerConfig {
  port: number;
  host: string;
  environment: 'development' | 'staging' | 'production';
  log_level: 'error' | 'warn' | 'info' | 'debug';
  enable_metrics: boolean;
  enable_health_check: boolean;
  enable_swagger: boolean;
  cors_enabled: boolean;
  compression_enabled: boolean;
  trust_proxy: boolean;
  request_timeout_ms: number;
  body_limit: string;
  security: WebhookSecurityConfig;
}

// Metrics Types
export interface WebhookMetrics {
  requests_total: number;
  requests_per_event_type: Record<WebhookEventType, number>;
  errors_total: number;
  errors_per_type: Record<string, number>;
  processing_duration_seconds: number[];
  rate_limit_exceeded_total: number;
  security_events_total: number;
  active_connections: number;
  memory_usage_bytes: number;
  cpu_usage_percent: number;
}

// Audit Log Types
export interface AuditLogEntry {
  timestamp: string;
  event_id: string;
  event_type: 'webhook_received' | 'security_event' | 'error' | 'warning';
  severity: 'info' | 'warn' | 'error' | 'critical';
  source: {
    ip: string;
    user_agent?: string;
    delivery_id?: string;
  };
  webhook?: {
    event_type: WebhookEventType;
    repository?: string;
    sender?: string;
    signature_valid: boolean;
    processing_time_ms: number;
  };
  security?: {
    ip_allowed: boolean;
    rate_limit_remaining: number;
    payload_size_bytes: number;
    sensitive_data_detected: boolean;
    threat_level?: 'low' | 'medium' | 'high' | 'critical';
  };
  error?: {
    code: string;
    message: string;
    stack?: string;
  };
  compliance: {
    gdpr_compliant: boolean;
    retention_days: number;
    encrypted: boolean;
  };
  metadata?: Record<string, unknown>;
}

// Validation Types
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings?: string[];
}

export interface SecurityCheckResult {
  passed: boolean;
  checks: {
    signature_valid: boolean;
    ip_allowed: boolean;
    rate_limit_ok: boolean;
    payload_size_ok: boolean;
    headers_valid: boolean;
    sensitive_data_detected: boolean;
  };
  threat_level: 'low' | 'medium' | 'high' | 'critical';
  actions_taken: string[];
}

// Error Types
export interface WebhookError extends Error {
  code: string;
  statusCode: number;
  details?: string;
  requestId?: string;
  deliveryId?: string;
  correlationId?: string;
}

export interface RateLimitError extends WebhookError {
  limit: number;
  remaining: number;
  resetTime: number;
  retryAfter: number;
}

// Health Check Types
export interface HealthCheckResult {
  status: 'healthy' | 'unhealthy' | 'degraded';
  timestamp: string;
  version: string;
  service: string;
  uptime_seconds: number;
  dependencies: {
    database?: 'healthy' | 'unhealthy';
    redis?: 'healthy' | 'unhealthy';
    elasticsearch?: 'healthy' | 'unhealthy';
  };
  checks: {
    memory_usage: boolean;
    disk_space: boolean;
    network_connectivity: boolean;
    external_services: boolean;
  };
}