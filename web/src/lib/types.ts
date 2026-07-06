export type RfiStatus =
  | "DRAFT"
  | "INVITED"
  | "CALL_READY"
  | "IN_CALL"
  | "SUMMARIZED"
  | "DELIVERED"
  | "NEEDS_REVIEW"
  | "CLOSED";

export type RfiCaseSummary = {
  id: string;
  customer_email: string;
  application_id?: string | null;
  status: RfiStatus;
  room_name?: string | null;
  magic_token?: string | null;
  expires_at?: string | null;
  needs_review?: boolean;
  review_reason?: string | null;
  created_at: string;
  updated_at: string;
};

export type Application = {
  application_id: string;
  customer_id: string;
  requested_loan_amount: number;
  requested_tenure_amount: number;
  issue_status?: string | null;
  created_at: string;
};

export type ApplicationList = {
  items: Application[];
  total: number;
};

export type RfiQuestion = {
  id: string;
  rfi_id: string;
  order_index: number;
  question_text: string;
};

export type RfiAnswer = {
  id: string;
  rfi_id: string;
  question_id: string;
  answer_text: string;
  answer_status: "answered" | "unclear" | "not_answered";
  evidence_quote?: string | null;
  follow_up_asked: boolean;
  evaluator_notes?: string | null;
  captured_by: "agent" | "customer_text";
  created_at: string;
};

export type RfiCustomerQuestion = {
  id: string;
  rfi_id: string;
  question_text: string;
  agent_response?: string | null;
  needs_human_followup: boolean;
  created_at: string;
};

export type RfiTranscriptTurn = {
  id: string;
  rfi_id: string;
  speaker: "agent" | "customer" | "system";
  text: string;
  created_at: string;
};

export type RfiSummary = {
  rfi_id: string;
  summary_text: string;
  structured_json: Record<string, unknown>;
  created_at: string;
};

export type RfiDetail = RfiCaseSummary & {
  questions: RfiQuestion[];
  answers: RfiAnswer[];
  customer_questions: RfiCustomerQuestion[];
  transcript: RfiTranscriptTurn[];
  summary?: RfiSummary | null;
};

export type CustomerRfiDetail = {
  id: string;
  customer_email: string;
  status: RfiStatus;
  room_name?: string | null;
  needs_review?: boolean;
  review_reason?: string | null;
  questions: RfiQuestion[];
  answers: RfiAnswer[];
  customer_questions: RfiCustomerQuestion[];
  summary?: RfiSummary | null;
};
