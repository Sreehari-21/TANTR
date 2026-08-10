export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  readonly isNetwork: boolean;

  constructor(message: string, isNetwork = false) {
    super(message);
    this.name = 'ApiError';
    this.isNetwork = isNetwork;
  }
}

function formatErrorDetail(detail: unknown): string {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((e) => {
        if (e && typeof e === 'object' && 'msg' in e) return String((e as { msg: string }).msg);
        return JSON.stringify(e);
      })
      .join(' ');
  }
  if (detail && typeof detail === 'object') return JSON.stringify(detail);
  return 'Request failed';
}

function networkMessage(): string {
  return `Cannot reach the TANTR API at ${API_BASE}. Start the backend: ./scripts/run-backend.sh`;
}

async function request(
  path: string,
  opts: RequestInit = {},
  token?: string | null
): Promise<Response> {
  const headers: Record<string, string> = {
    ...(opts.headers as Record<string, string>),
  };
  if (opts.body !== undefined && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }
  const auth = token !== undefined ? token : getToken();
  if (auth) headers['Authorization'] = `Bearer ${auth}`;

  try {
    return await fetch(`${API_BASE}${path}`, { ...opts, headers });
  } catch {
    throw new ApiError(networkMessage(), true);
  }
}

export type User = {
  id: number;
  email: string;
  username: string;
  full_name: string | null;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
};

export type Enquiry = {
  id: number;
  name: string;
  email: string;
  subject: string;
  message: string;
  created_at: string;
};

export type Repo = {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
  head_sha?: string | null;
  created_at: string;
};

export type Commit = {
  id: number;
  repository_id: number;
  sha: string;
  tree_sha?: string | null;
  parent_sha?: string | null;
  message: string | null;
  author_name: string | null;
  author_email: string | null;
  created_at: string;
};

export type CommitAnalysis = {
  id: number;
  commit_id: number;
  static_analysis_raw?: Record<string, unknown> | null;
  complexity_score: number | null;
  style_score: number | null;
  documentation_score: number | null;
  warnings: string[] | null;
  ai_feedback: string | null;
  ai_suggestions: string[] | null;
  status: string;
  created_at: string;
};

export type Grade = {
  id: number;
  commit_id: number;
  code_quality: number | null;
  efficiency: number | null;
  documentation: number | null;
  testing: number | null;
  commit_consistency: number | null;
  final_score: number;
  created_at: string;
};

function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('tantr_token');
}

export async function checkApiHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`, { method: 'GET' });
    return res.ok;
  } catch {
    return false;
  }
}

export async function api<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await request(path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(formatErrorDetail(err.detail) || String(err));
  }
  return res.json();
}

export async function login(username: string, password: string): Promise<{ access_token: string }> {
  const res = await request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new ApiError(formatErrorDetail(data.detail) || 'Login failed');
  return data;
}

export async function register(data: {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}): Promise<User> {
  return api('/api/auth/register', { method: 'POST', body: JSON.stringify(data) });
}

export async function getMe(): Promise<User> {
  return api('/api/auth/me');
}

export async function getRepos(): Promise<Repo[]> {
  return api('/api/repos');
}

export async function getRepo(id: number): Promise<Repo> {
  return api(`/api/repos/${id}`);
}

export async function createRepo(data: { name: string; description?: string }): Promise<Repo> {
  return api('/api/repos', { method: 'POST', body: JSON.stringify(data) });
}

export async function getCommits(repoId: number): Promise<Commit[]> {
  return api(`/api/repos/${repoId}/commits`);
}

export async function createCommit(
  repoId: number,
  data: { message: string; files: Record<string, string> }
): Promise<Commit> {
  return api(`/api/repos/${repoId}/commits`, { method: 'POST', body: JSON.stringify(data) });
}

export async function getCommitAnalysis(
  repoId: number,
  commitId: number
): Promise<Commit & { analysis?: CommitAnalysis; grade?: Grade }> {
  return api(`/api/repos/${repoId}/commits/${commitId}/analysis`);
}

export async function getCommitDiff(repoId: number, commitId: number): Promise<string> {
  const res = await request(`/api/repos/${repoId}/commits/${commitId}/diff`, {}, getToken());
  if (!res.ok) throw new ApiError('Failed to fetch diff');
  return res.text();
}

export async function getCommitFiles(
  repoId: number,
  commitId: number
): Promise<{ sha: string; files: Record<string, string> }> {
  return api(`/api/repos/${repoId}/commits/${commitId}/files`);
}

export async function getRepoTree(
  repoId: number
): Promise<{ sha: string | null; files: Record<string, string> }> {
  return api(`/api/repos/${repoId}/tree`);
}

export async function triggerAnalyze(
  repoId: number,
  commitId: number
): Promise<{ status: string }> {
  return api(`/api/repos/${repoId}/commits/${commitId}/analyze`, { method: 'POST' });
}

export async function getAdminEnquiries(): Promise<Enquiry[]> {
  return api('/api/admin/enquiries');
}

export async function submitEnquiry(data: {
  name: string;
  email: string;
  subject: string;
  message: string;
}): Promise<Enquiry> {
  return api('/api/enquiries/', { method: 'POST', body: JSON.stringify(data) });
}
