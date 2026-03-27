import { z } from 'zod'

// --- Zod schemas for runtime validation ---

export const HealthStatusSchema = z.enum(['healthy', 'degraded', 'unhealthy', 'unknown'])

export const PushStateSchema = z.enum(['IDLE', 'PUSH_PENDING', 'APPLYING', 'APPLIED', 'FAILED'])

export const CollectorSummarySchema = z.object({
  instance_uid: z.string(),
  last_seen: z.number(),
  health_status: HealthStatusSchema,
  capabilities: z.number(),
})

export const HealthSnapshotSchema = z.object({
  recorded_at: z.number(),
  healthy: z.boolean(),
  status: z.string().nullable(),
  last_error: z.string().nullable(),
})

export const EffectiveConfigSchema = z.object({
  recorded_at: z.number(),
  config_hash: z.string(),
  config_json: z.record(z.string(), z.object({
    body: z.string(),
    content_type: z.string(),
  })),
})

export const PushStatusSchema = z.object({
  push_state: PushStateSchema,
  pending_config_hash: z.string().nullable(),
})

export const CollectorDetailSchema = z.object({
  instance_uid: z.string(),
  first_seen: z.number(),
  last_seen: z.number(),
  health_status: HealthStatusSchema,
  capabilities: z.number(),
  health_history: z.array(HealthSnapshotSchema),
  effective_config: EffectiveConfigSchema.nullable(),
  push_status: PushStatusSchema,
})

// --- TypeScript types inferred from schemas ---

export type HealthStatus = z.infer<typeof HealthStatusSchema>
export type PushState = z.infer<typeof PushStateSchema>
export type CollectorSummary = z.infer<typeof CollectorSummarySchema>
export type HealthSnapshot = z.infer<typeof HealthSnapshotSchema>
export type EffectiveConfig = z.infer<typeof EffectiveConfigSchema>
export type PushStatus = z.infer<typeof PushStatusSchema>
export type CollectorDetail = z.infer<typeof CollectorDetailSchema>

// --- Utility ---

export function extractYaml(config: EffectiveConfig | null): string {
  if (!config) return ''
  const entry = config.config_json['collector.yaml']
  return entry?.body ?? ''
}
