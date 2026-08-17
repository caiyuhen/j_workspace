import type {
  ScreeningStage,
  ScreeningDecision,
  ExcludeReasonJson,
  PrismaOverride,
  LiteratureStatsW82B,
} from '@meda/shared-sdk';
// TypeScript strict literal type assignment（任何一项 undefined 编译即 FAIL）
const _s1: ScreeningStage = 'ta';
const _s2: ScreeningStage = 'fulltext';
const _d1: ScreeningDecision = 'include';
const _d2: ScreeningDecision = 'exclude';
const _e: ExcludeReasonJson = {
  preset_class: 1,
  note: null,
  stage: null,
  auto_by: 'dedup_level4',
};
const _ep: ExcludeReasonJson = { preset_class: 9, note: '样本量不足 N<50' };
const _p: PrismaOverride = {
  identification: 1200,
  screening: null,
  eligibility: 980,
  included: 42,
  applied_at: '2026-08-17T00:00:00Z',
};
const _stats: LiteratureStatsW82B = {
  prisma_identification: 1200,
  prisma_screening: 1200,
  prisma_screening_exclude_ta: 100,
  prisma_screening_exclude_duplicate: 120,
  prisma_eligibility: 980,
  prisma_eligibility_exclude_fulltext: 938,
  prisma_included: 42,
  prisma_override_applied: false,
  prisma_diff_percent: null,
};
export { _s1, _s2, _d1, _d2, _e, _ep, _p, _stats };
