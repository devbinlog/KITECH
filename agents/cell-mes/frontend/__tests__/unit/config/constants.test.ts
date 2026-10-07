import { describe, it, expect } from 'vitest'
import { POLLING, STALE_TIME, API_TIMEOUT, PAGE_SIZE } from '@/config/constants'

describe('constants', () => {
  describe('POLLING', () => {
    it('has correct values for each interval', () => {
      expect(POLLING.FAST).toBe(5000)
      expect(POLLING.LOT_TRACE).toBe(10000)
      expect(POLLING.NORMAL).toBe(30000)
      expect(POLLING.SLOW).toBe(60000)
    })

    it('all values are positive numbers in expected range', () => {
      for (const value of Object.values(POLLING)) {
        expect(value).toBeGreaterThanOrEqual(1000)
        expect(value).toBeLessThanOrEqual(120000)
      }
    })
  })

  describe('STALE_TIME', () => {
    it('has correct values', () => {
      expect(STALE_TIME.DEFAULT).toBe(5000)
      expect(STALE_TIME.SHORT).toBe(30000)
      expect(STALE_TIME.MEDIUM).toBe(300000)
      expect(STALE_TIME.LONG).toBe(600000)
    })

    it('SHORT is greater than DEFAULT', () => {
      expect(STALE_TIME.SHORT).toBeGreaterThan(STALE_TIME.DEFAULT)
    })

    it('MEDIUM is greater than SHORT', () => {
      expect(STALE_TIME.MEDIUM).toBeGreaterThan(STALE_TIME.SHORT)
    })

    it('LONG is greater than MEDIUM', () => {
      expect(STALE_TIME.LONG).toBeGreaterThan(STALE_TIME.MEDIUM)
    })
  })

  describe('API_TIMEOUT', () => {
    it('LLM timeout is 30000', () => {
      expect(API_TIMEOUT.LLM).toBe(30000)
    })
  })

  describe('PAGE_SIZE', () => {
    it('has correct values for each page size', () => {
      expect(PAGE_SIZE.DEFAULT).toBe(20)
      expect(PAGE_SIZE.HISTORY).toBe(50)
      expect(PAGE_SIZE.WORK_ORDERS).toBe(100)
      expect(PAGE_SIZE.ALL_ORDERS).toBe(1000)
    })
  })
})
