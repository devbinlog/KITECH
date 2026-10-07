/**
 * Unit tests for SPC (Statistical Process Control) calculation logic.
 * The calculateCapabilityIndices function lives in app/(main)/quality/spc/page.tsx
 * and is tested here by extracting its pure logic.
 *
 * Formulas:
 *   Cp  = (USL - LSL) / (6σ)
 *   Cpk = min((USL - mean) / (3σ), (mean - LSL) / (3σ))
 *   σ   = sample standard deviation
 */
import { describe, it, expect } from 'vitest'
import type { SPCData } from '@/types'

// Extract the pure calculation function for testing.
// This mirrors the logic in app/(main)/quality/spc/page.tsx calculateCapabilityIndices.
interface CapabilityResult {
  cp: number
  cpk: number
  mean: number
  stdDev: number
}

function calculateCapabilityIndices(
  spcData: SPCData[],
  usl: number | null | undefined,
  lsl: number | null | undefined
): CapabilityResult | null {
  if (!spcData.length || !usl || !lsl) return null

  const values = spcData.flatMap(d => d.sample_values)
  if (values.length < 2) return null

  const mean = values.reduce((sum, val) => sum + val, 0) / values.length
  const variance =
    values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) /
    (values.length - 1)
  const stdDev = Math.sqrt(variance)

  if (stdDev === 0) return { cp: 0, cpk: 0, mean, stdDev }

  const cp = (usl - lsl) / (6 * stdDev)
  const cpk = Math.min(
    (usl - mean) / (3 * stdDev),
    (mean - lsl) / (3 * stdDev)
  )

  return { cp, cpk, mean, stdDev }
}

// Helper to create SPCData with sample_values
function makeSPCData(sampleValueGroups: number[][]): SPCData[] {
  return sampleValueGroups.map((sample_values, i) => ({
    id: i + 1,
    inspection_item_id: 1,
    sample_date: `2024-01-0${i + 1}T00:00:00Z`,
    sample_values,
    x_bar: sample_values.reduce((a, b) => a + b, 0) / sample_values.length,
    r_value: Math.max(...sample_values) - Math.min(...sample_values),
    ucl_x: 10.5,
    lcl_x: 9.5,
    ucl_r: 1.0,
    lcl_r: 0,
  }))
}

describe('calculateCapabilityIndices', () => {
  describe('normal calculation', () => {
    it('returns correct Cp for centered process', () => {
      // Values centered at 10 with known spread
      const data = makeSPCData([[9.8, 10.2], [9.9, 10.1], [10.0, 10.0]])
      const result = calculateCapabilityIndices(data, 11, 9)

      expect(result).not.toBeNull()
      // (11 - 9) / (6 * stdDev) — stdDev is small for these values
      expect(result!.cp).toBeGreaterThan(0)
      expect(typeof result!.cp).toBe('number')
    })

    it('Cp = (USL - LSL) / (6 * stdDev)', () => {
      // Simple dataset: [9, 10, 11] → mean=10, variance=1, stdDev=1
      const data = makeSPCData([[9, 10, 11]])
      const result = calculateCapabilityIndices(data, 13, 7)

      expect(result).not.toBeNull()
      // stdDev = 1, Cp = (13-7)/(6*1) = 1.0
      expect(result!.cp).toBeCloseTo(1.0, 5)
    })

    it('Cpk = min((USL-mean)/3σ, (mean-LSL)/3σ)', () => {
      // [9, 10, 11] → mean=10, stdDev=1
      // USL=13, LSL=7 → Cpk = min((13-10)/3, (10-7)/3) = min(1, 1) = 1
      const data = makeSPCData([[9, 10, 11]])
      const result = calculateCapabilityIndices(data, 13, 7)

      expect(result!.cpk).toBeCloseTo(1.0, 5)
    })

    it('Cpk is smaller than Cp when process is off-center', () => {
      // Values skewed toward USL: [10.5, 10.6, 10.7]
      const data = makeSPCData([[10.5, 10.6, 10.7]])
      const result = calculateCapabilityIndices(data, 11, 9)

      expect(result).not.toBeNull()
      expect(result!.cpk).toBeLessThan(result!.cp)
    })

    it('returns correct mean value', () => {
      const data = makeSPCData([[8, 10, 12], [9, 11]])
      const result = calculateCapabilityIndices(data, 15, 5)

      // All values: [8, 10, 12, 9, 11] → mean = 50/5 = 10
      expect(result!.mean).toBeCloseTo(10, 5)
    })

    it('returns positive stdDev', () => {
      const data = makeSPCData([[9.8, 10.2], [10.0, 10.0]])
      const result = calculateCapabilityIndices(data, 12, 8)

      expect(result!.stdDev).toBeGreaterThan(0)
    })
  })

  describe('edge cases', () => {
    it('returns null when spcData is empty', () => {
      const result = calculateCapabilityIndices([], 11, 9)
      expect(result).toBeNull()
    })

    it('returns null when usl is null', () => {
      const data = makeSPCData([[9, 10, 11]])
      const result = calculateCapabilityIndices(data, null, 7)
      expect(result).toBeNull()
    })

    it('returns null when lsl is null', () => {
      const data = makeSPCData([[9, 10, 11]])
      const result = calculateCapabilityIndices(data, 13, null)
      expect(result).toBeNull()
    })

    it('returns null when usl is undefined', () => {
      const data = makeSPCData([[9, 10, 11]])
      const result = calculateCapabilityIndices(data, undefined, 7)
      expect(result).toBeNull()
    })

    it('returns null when values.length < 2 (single value)', () => {
      // Only one sample_value total across all data points
      const data = makeSPCData([[10]])
      const result = calculateCapabilityIndices(data, 13, 7)
      expect(result).toBeNull()
    })

    it('returns cp=0, cpk=0 when stdDev === 0 (all values identical)', () => {
      // All values are 10 → stdDev = 0
      const data = makeSPCData([[10, 10], [10, 10]])
      const result = calculateCapabilityIndices(data, 12, 8)

      expect(result).not.toBeNull()
      expect(result!.cp).toBe(0)
      expect(result!.cpk).toBe(0)
      expect(result!.mean).toBe(10)
      expect(result!.stdDev).toBe(0)
    })

    it('handles multiple data points with sample_values each', () => {
      const data = makeSPCData([
        [9.9, 10.1],
        [9.8, 10.2],
        [10.0, 10.0],
        [9.95, 10.05],
      ])
      const result = calculateCapabilityIndices(data, 11, 9)

      expect(result).not.toBeNull()
      expect(result!.cp).toBeGreaterThan(0)
      expect(result!.cpk).toBeGreaterThan(0)
    })

    it('Cpk can be negative when process mean is outside spec limits', () => {
      // Mean ~15, USL=13, LSL=7 → (USL-mean)/3σ is negative
      const data = makeSPCData([[14, 15, 16]])
      const result = calculateCapabilityIndices(data, 13, 7)

      expect(result).not.toBeNull()
      expect(result!.cpk).toBeLessThan(0)
    })
  })

  describe('high capability indices', () => {
    it('returns Cp >= 1.33 for a very capable process', () => {
      // Tight process: mean=10, values 9.99..10.01, wide spec 8-12
      const data = makeSPCData([[9.99, 10.01], [9.995, 10.005], [9.998, 10.002]])
      const result = calculateCapabilityIndices(data, 12, 8)

      expect(result).not.toBeNull()
      expect(result!.cp).toBeGreaterThan(1.33)
    })
  })
})
