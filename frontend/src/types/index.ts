export type Role = 'OWNER' | 'ADMIN' | 'MEMBER' | 'VIEWER';
export type UserStatus = 'ACTIVE' | 'DISABLED' | 'PENDING_INVITE';
export type MemberStatus = 'INVITED' | 'ACTIVE' | 'SUSPENDED' | 'REMOVED';
export type ApiKeyStatus = 'ACTIVE' | 'REVOKED' | 'EXPIRED';

export type AuthUserView = {
  id: string;
  email: string;
  displayName: string;
  role: Role;
  orgId: string;
  status: UserStatus;
};

export type AuthTokenResponse = {
  accessToken: string;
  tokenType: 'Bearer';
  expiresIn: number;
  user: AuthUserView;
};

export type RefreshResponse = {
  accessToken: string;
  tokenType: 'Bearer';
  expiresIn: number;
};

export type CapabilityStatus =
  | 'SUPPORTED'
  | 'PARTIALLY_SUPPORTED'
  | 'NOT_SUPPORTED'
  | 'NEED_MORE_INFO';

export type SessionStatus = 'PROCESSING' | 'DONE' | 'FAILED';
export type ReviewViewStatus = SessionStatus | 'NOT_FOUND';
export type ConfidenceLevel = 'high' | 'medium' | 'low';
export type FileParseStatus = 'PENDING' | 'PARSING' | 'DONE' | 'FAILED';

export type UploadedFileRef = {
  fileId: string;
  fileName: string;
  fileSize: number;
  parseStatus: FileParseStatus;
};

export type CreatePreReviewForm = {
  requirementText: string;
  backgroundText?: string;
  businessDomain?: string;
  moduleHint?: string;
  attachments?: UploadedFileRef[];
};

export type EvidenceItem = {
  doc_id: string;
  doc_title: string;
  chunk_id: string;
  snippet: string;
  source_type: string;
  relevance_score: number;
  trust_level: string;
};

export type PreReviewReportView = {
  sessionId: string;
  parentSessionId?: string | null;
  version: number;
  status: SessionStatus;
  summary: string;
  capability: {
    status: CapabilityStatus;
    reason: string;
    confidence?: ConfidenceLevel | null;
  };
  evidence: EvidenceItem[];
  structuredRequirement: {
    goal: string;
    actors: string[];
    scope: string[];
    constraints: string[];
    expectedOutput: string;
  };
  missingInfo: string[];
  risks: Array<{ title: string; description: string; level: 'high' | 'medium' | 'low' }>;
  impactScope: string[];
  nextActions: string[];
  uncertainties: string[];
  errorCode?: string | null;
  errorMessage?: string | null;
};

export type HistoryQuery = {
  keyword?: string;
  capabilityStatus?: CapabilityStatus;
  page: number;
  pageSize: number;
};

export type HistoryItem = {
  sessionId: string;
  requestText: string;
  capabilityStatus: CapabilityStatus;
  version: number;
  createdAt: string;
};

export type HistoryListResponse = {
  total: number;
  page: number;
  pageSize: number;
  items: HistoryItem[];
};

export type ListResponse<T> = {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
};

export type CreateUserRequest = {
  email: string;
  displayName: string;
  role: Role;
  orgId?: string;
};

export type ListUsersQuery = {
  query?: string;
  role?: Role;
  status?: UserStatus;
  page: number;
  pageSize: number;
};

export type UserListItem = {
  id: string;
  email: string;
  displayName: string;
  role: Role;
  status: UserStatus;
  orgId: string;
  createdAt: string;
  lastLoginAt: string | null;
};

export type UpdateUserStatusRequest = {
  status: UserStatus;
};

export type UpdateUserRoleRequest = {
  role: Role;
};

export type ListMembersQuery = {
  query?: string;
  permissionRole?: Role;
  memberStatus?: MemberStatus;
  functionalRoleId?: string;
  page: number;
  pageSize: number;
};

export type MemberListItem = {
  membershipId: string;
  userId: string;
  email: string;
  displayName: string;
  permissionRole: Role;
  memberStatus: MemberStatus;
  functionalRoleId: string;
  functionalRoleCode: string;
  functionalRoleName: string;
  orgId: string;
  createdAt: string;
  lastLoginAt: string | null;
};

export type UpdateMemberRoleRequest = {
  role: Role;
  reason?: string;
};

export type UpdateMemberStatusRequest = {
  status: MemberStatus;
  reason?: string;
};

export type UpdateMemberFunctionalRoleRequest = {
  functionalRoleId: string;
  reason?: string;
};

export type ListFunctionalRolesQuery = {
  isActive?: boolean;
  page: number;
  pageSize: number;
};

export type FunctionalRoleView = {
  id: string;
  orgId: string;
  code: string;
  name: string;
  description?: string | null;
  isActive: boolean;
  sortOrder: number;
  createdAt: string;
  updatedAt: string;
};

export type CreateFunctionalRoleRequest = {
  code: string;
  name: string;
  description?: string;
};

export type UpdateFunctionalRoleStatusRequest = {
  isActive: boolean;
};

export type IssueApiKeyRequest = {
  userId: string;
  name: string;
  expiresAt?: string;
};

export type IssueApiKeyResponse = {
  keyId: string;
  keyPrefix: string;
  plainTextKey: string;
  expiresAt: string | null;
};

export type ListApiKeysQuery = {
  userId?: string;
  status?: ApiKeyStatus;
  page: number;
  pageSize: number;
};

export type ApiKeyListItem = {
  keyId: string;
  userId: string;
  keyPrefix: string;
  status: ApiKeyStatus;
  name: string;
  expiresAt: string | null;
  lastUsedAt: string | null;
  createdAt: string;
};

export type ListAuditLogsQuery = {
  actorUserId?: string;
  action?: string;
  page: number;
  pageSize: number;
};

export type AuditLogItem = {
  id: string;
  actorUserId: string | null;
  actorEmail: string | null;
  action: string;
  targetType: string | null;
  targetId: string | null;
  result: string | null;
  createdAt: string;
};
