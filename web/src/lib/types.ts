export type RfiStatus =
  | "DRAFT"
  | "INVITED"
  | "CALL_READY"
  | "IN_CALL"
  | "SUMMARIZED"
  | "DELIVERED"
  | "CLOSED";

export type RfiCaseSummary = {
  id: string;
  customer_email: string;
  application_id?: string | null;
  status: RfiStatus;
  room_name?: string | null;
  magic_token?: string | null;
  expires_at?: string | null;
  created_at: string;
  updated_at: string;
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
  captured_by: "agent" | "customer_text";
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
  summary?: RfiSummary | null;
};

export type CustomerRfiDetail = {
  id: string;
  customer_email: string;
  status: RfiStatus;
  room_name?: string | null;
  questions: RfiQuestion[];
  answers: RfiAnswer[];
  summary?: RfiSummary | null;
};
