import { describe, it, expect } from 'vitest'
import { CollectorSummarySchema } from '@/api/types'

describe('API types', () => {
  it('validates a valid CollectorSummary', () => {
    const input = {
      instance_uid: 'aabbccddeeff00112233445566778899',
      last_seen: 1700000000000000000,
      health_status: 'healthy',
      capabilities: 19463,
    }
    const result = CollectorSummarySchema.parse(input)
    expect(result.instance_uid).toBe('aabbccddeeff00112233445566778899')
    expect(result.health_status).toBe('healthy')
  })

  it('rejects invalid health_status', () => {
    const input = {
      instance_uid: 'aabbccddeeff00112233445566778899',
      last_seen: 1700000000000000000,
      health_status: 'invalid',
      capabilities: 19463,
    }
    expect(() => CollectorSummarySchema.parse(input)).toThrow()
  })
})
