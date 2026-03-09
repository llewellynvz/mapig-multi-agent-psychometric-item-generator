import { z } from "zod";

/**
 * Zod schema aligned with MAPIG API UserRequest.
 */
export const instrumentSetupSchema = z.object({
  model_provider: z.enum(["claude", "openai"]).default("claude"),
  use_chatgpt_critics: z.boolean().default(true),
  construct_name: z
    .string()
    .min(2, "Construct name must be at least 2 characters"),
  construct_definition: z
    .string()
    .min(10, "Construct definition must be at least 10 characters"),
  target_population: z
    .string()
    .min(2, "Target population must be at least 2 characters"),
  response_scale: z
    .string()
    .min(2, "Response scale is required"),
  item_count: z
    .number()
    .min(2, "Minimum 2 items")
    .max(50, "Maximum 50 items"),
  constraints: z.array(z.string()).default([]),
  construct_exclusions: z.string().optional(),
  native_construct: z.string().optional(),
  example_item: z.string().optional(),
  approved_domains: z.array(z.string()).default([]),
});

export type InstrumentSetupFormValues = z.infer<typeof instrumentSetupSchema>;

export const RESPONSE_SCALE_PRESETS = [
  "5-point Likert: Strongly disagree → Strongly agree",
  "7-point Likert: Strongly disagree → Strongly agree",
  "Frequency: Never → Always",
  "Agreement: Not at all → Completely",
] as const;

export const DEFAULT_CONSTRAINTS = [
  "No double-barrelled items",
  "Avoid idioms",
  "Minimize reading level",
  "Positively keyed only",
];

export const DEFAULT_APPROVED_DOMAINS = [
  "doi.org",
  "psycnet.apa.org",
  "link.springer.com",
  "sciencedirect.com",
  "onlinelibrary.wiley.com",
  "tandfonline.com",
  "journals.sagepub.com",
  "academic.oup.com",
  "cambridge.org",
];

export const defaultInstrumentSetup: InstrumentSetupFormValues = {
  model_provider: "claude",
  use_chatgpt_critics: true,
  construct_name: "",
  construct_definition: "",
  target_population: "",
  response_scale: RESPONSE_SCALE_PRESETS[0],
  item_count: 10,
  constraints: [...DEFAULT_CONSTRAINTS],
  construct_exclusions: "",
  native_construct: "",
  example_item: "",
  approved_domains: [...DEFAULT_APPROVED_DOMAINS],
};
