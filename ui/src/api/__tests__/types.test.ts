import { describe, it, expect } from 'vitest'
import { extractYaml } from '@/api/types'
import type { EffectiveConfig } from '@/api/types'

function makeConfig(entries: Record<string, { body: string; content_type: string }>): EffectiveConfig {
  return { recorded_at: 0, config_hash: 'abc', config_json: entries }
}

describe('extractYaml', () => {
  it('returns empty string for null config', () => {
    expect(extractYaml(null)).toBe('')
  })

  it('returns body for canonical collector.yaml key', () => {
    const config = makeConfig({ 'collector.yaml': { body: 'receivers: {}', content_type: 'text/yaml' } })
    expect(extractYaml(config)).toBe('receivers: {}')
  })

  it('falls back to first entry when collector.yaml key is absent', () => {
    // OTel Collector reports its locally-loaded config under "" before any push
    const config = makeConfig({ '': { body: 'exporters: {}', content_type: 'text/yaml' } })
    expect(extractYaml(config)).toBe('exporters: {}')
  })

  it('prefers collector.yaml over other keys when both present', () => {
    const config = makeConfig({
      '': { body: 'old config', content_type: 'text/yaml' },
      'collector.yaml': { body: 'pushed config', content_type: 'text/yaml' },
    })
    expect(extractYaml(config)).toBe('pushed config')
  })

  it('returns empty string when config_json is empty', () => {
    const config = makeConfig({})
    expect(extractYaml(config)).toBe('')
  })
})
