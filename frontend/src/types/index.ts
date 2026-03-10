export type CapabilityStatus =
  | 'SUPPORTED'
  | 'PARTIALLY_SUPPORTED'
  | 'NOT_SUPPORTED'
  | 'NEED_MORE_INFO';

export type ReviewStatus = 'PROCESSING' | 'DONE' | 'FAILED' | 'NOT_FOUND';

export type UploadedFileRef = {
  fileId: string;
  fileName: string;
  fileSize: number;
  parseStatus?: string;
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
  status: ReviewStatus;
  summary: string;
  capability: {
    status: CapabilityStatus;
    reason: string;
    confidence: 'high' | 'medium' | 'low';
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
