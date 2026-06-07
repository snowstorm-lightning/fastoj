import { z } from "zod";

export const testCaseResultSchema = z.object({
  id: z.string(),
  testcase_id: z.string().nullable().optional(),
  status: z.string(),
  input: z.string().nullable().optional(),
  expected_output: z.string().nullable().optional(),
  actual_output: z.string().nullable().optional(),
  execute_time: z.number().nullable().optional(),
  memory_used: z.number().nullable().optional(),
  is_hidden: z.boolean(),
});

export const submissionDetailSchema = z.object({
  id: z.string(),
  problem_id: z.string(),
  user_id: z.string(),
  code: z.string(),
  language: z.string(),
  status: z.string(),
  result: z.string().nullable().optional(),
  error_message: z.string().nullable().optional(),
  execute_time: z.number().nullable().optional(),
  memory_used: z.number().nullable().optional(),
  score: z.number(),
  created_at: z.string(),
  finished_at: z.string().nullable().optional(),
  testcase_results: z.array(testCaseResultSchema).default([]),
});

export const problemListItemSchema = z.object({
  id: z.string(),
  title: z.string(),
  slug: z.string(),
  difficulty: z.string(),
  tags: z.array(z.string()),
  total_submissions: z.number(),
  accepted_submissions: z.number(),
  ac_rate: z.number(),
  is_public: z.boolean(),
  mode: z.string().default("acm"),
  function_signature: z.string().nullable().optional(),
  created_at: z.string(),
});

export const problemDetailSchema = z.object({
  id: z.string(),
  title: z.string(),
  slug: z.string(),
  description: z.string(),
  difficulty: z.string(),
  tags: z.array(z.string()),
  time_limit: z.number(),
  memory_limit: z.number(),
  hint: z.string().nullable().optional(),
  mode: z.string().default("acm"),
  input_format: z.string().nullable().optional(),
  output_format: z.string().nullable().optional(),
  function_signature: z.string().nullable().optional(),
  total_submissions: z.number(),
  accepted_submissions: z.number(),
  ac_rate: z.number(),
  sample_testcases: z.array(z.object({
    input: z.string(),
    output: z.string(),
    explanation: z.string().nullable().optional(),
    acm_input: z.string().nullable().optional(),
    acm_output: z.string().nullable().optional(),
    function_input: z.string().nullable().optional(),
    function_output: z.string().nullable().optional(),
    display_mode: z.string().nullable().optional(),
  })),
  created_at: z.string(),
});

export type ProblemDiscussion = {
  id: string;
  problem_id: string;
  user_id: string;
  author: string;
  body: string;
  created_at: string;
  updated_at?: string | null;
  parent_id?: string | null;
  like_count: number;
  liked_by_me: boolean;
  reply_count: number;
  can_delete: boolean;
  is_deleted: boolean;
  is_template: boolean;
  replies: ProblemDiscussion[];
};

export const problemDiscussionSchema: z.ZodType<ProblemDiscussion> = z.lazy(() =>
  z.object({
    id: z.string(),
    problem_id: z.string(),
    user_id: z.string(),
    author: z.string(),
    body: z.string(),
    created_at: z.string(),
    updated_at: z.string().nullable().optional(),
    parent_id: z.string().nullable().optional(),
    like_count: z.number().int().nonnegative().default(0),
    liked_by_me: z.boolean().default(false),
    reply_count: z.number().int().nonnegative().default(0),
    can_delete: z.boolean().default(false),
    is_deleted: z.boolean().default(false),
    is_template: z.boolean().default(false),
    replies: z.array(problemDiscussionSchema).default([]),
  }) as z.ZodType<ProblemDiscussion>,
);

export const aiExplainSchema = z.object({
  summary: z.string(),
  verdict: z.enum([
    "accepted",
    "wrong_answer",
    "time_limit",
    "memory_limit",
    "compile_error",
    "runtime_error",
    "system_error",
    "unknown",
  ]),
  likely_causes: z.array(z.string()),
  suspicious_code_regions: z.array(
    z.object({
      line_start: z.number().nullable(),
      line_end: z.number().nullable(),
      reason: z.string(),
    }),
  ),
  public_case_analysis: z.array(
    z.object({
      case_index: z.number(),
      observation: z.string(),
      expected_summary: z.string(),
      actual_summary: z.string(),
    }),
  ),
  minimal_fix_hint: z.string(),
  edge_cases_to_check: z.array(z.string()),
  complexity_comment: z.string(),
  next_action: z.string(),
  full_solution_revealed: z.literal(false),
});

export const aiReviewSchema = z.object({
  summary: z.string(),
  risks: z.array(z.string()),
  io_format_notes: z.array(z.string()),
  edge_cases_to_check: z.array(z.string()),
  complexity_comment: z.string(),
  suggested_next_action: z.string(),
});

export const aiHintSchema = z.object({
  level: z.union([z.literal(1), z.literal(2), z.literal(3)]),
  hint: z.string(),
  focus: z.array(z.string()),
  full_solution_revealed: z.literal(false),
});

export const aiChatSchema = z.object({
  message: z.string(),
  suggested_actions: z.array(z.string()),
  full_solution_revealed: z.literal(false),
});

export type ProblemListItem = z.infer<typeof problemListItemSchema>;
export type ProblemDetail = z.infer<typeof problemDetailSchema>;
export type SubmissionDetail = z.infer<typeof submissionDetailSchema>;
export type AIExplain = z.infer<typeof aiExplainSchema>;
export type AIReview = z.infer<typeof aiReviewSchema>;
export type AIHint = z.infer<typeof aiHintSchema>;
export type AIChat = z.infer<typeof aiChatSchema>;
