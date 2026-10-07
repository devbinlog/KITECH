import { describe, it, expect } from 'vitest'
import { SOLVER_OPTIONS, SCHEDULING_MODES } from '@/hooks/useScheduler'

describe('useScheduler constants', () => {
  describe('SOLVER_OPTIONS', () => {
    it('has 5 entries', () => {
      expect(SOLVER_OPTIONS).toHaveLength(5)
    })

    it('each option has value, label, and description properties', () => {
      for (const option of SOLVER_OPTIONS) {
        expect(option).toHaveProperty('value')
        expect(option).toHaveProperty('label')
        expect(option).toHaveProperty('description')
        expect(typeof option.value).toBe('string')
        expect(typeof option.label).toBe('string')
        expect(typeof option.description).toBe('string')
      }
    })

    it('contains the expected solver values', () => {
      const values = SOLVER_OPTIONS.map((o) => o.value)
      expect(values).toEqual(['OR_TOOLS', 'GA', 'SA', 'TABU', 'ALNS'])
    })
  })

  describe('SCHEDULING_MODES', () => {
    it('has 3 entries', () => {
      expect(SCHEDULING_MODES).toHaveLength(3)
    })

    it('contains the expected mode values', () => {
      const values = SCHEDULING_MODES.map((m) => m.value)
      expect(values).toEqual(['new', 'reschedule', 'full_rebalance'])
    })

    it('each mode has include_running, include_scheduled, and severity properties', () => {
      for (const mode of SCHEDULING_MODES) {
        expect(mode).toHaveProperty('include_running')
        expect(mode).toHaveProperty('include_scheduled')
        expect(mode).toHaveProperty('severity')
        expect(typeof mode.include_running).toBe('boolean')
        expect(typeof mode.include_scheduled).toBe('boolean')
        expect(typeof mode.severity).toBe('string')
      }
    })

    it('"new" mode has correct configuration', () => {
      const newMode = SCHEDULING_MODES.find((m) => m.value === 'new')!
      expect(newMode.include_running).toBe(false)
      expect(newMode.include_scheduled).toBe(false)
      expect(newMode.severity).toBe('info')
    })

    it('"full_rebalance" mode has correct configuration', () => {
      const fullMode = SCHEDULING_MODES.find((m) => m.value === 'full_rebalance')!
      expect(fullMode.include_running).toBe(true)
      expect(fullMode.include_scheduled).toBe(true)
      expect(fullMode.severity).toBe('danger')
    })
  })
})
