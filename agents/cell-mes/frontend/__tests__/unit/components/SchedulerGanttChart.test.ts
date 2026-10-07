/**
 * Unit tests for pure helper functions extracted from SchedulerGanttChart.tsx
 * We test: getTaskColor, isDowntimeTask, getTaskStyle (position/width logic),
 * and the footer task counting logic.
 */
import { describe, it, expect } from 'vitest'
import type { ScheduledTaskForGantt } from '@/components/scheduler/SchedulerGanttChart'

// --- Extracted pure functions (mirrored from SchedulerGanttChart.tsx) ---

const HOUR_WIDTH = 60 // 1 hour = 60px

const STATUS_COLORS = {
  scheduled: 'bg-blue-200 border-blue-400 text-blue-800',
  running: 'bg-green-200 border-green-400 text-green-800',
  completed: 'bg-gray-200 border-gray-400 text-gray-600',
  paused: 'bg-yellow-200 border-yellow-400 text-yellow-800',
  error: 'bg-red-200 border-red-400 text-red-800',
  downtime: 'border-red-400 text-red-800',
}

const isDowntimeTask = (task: ScheduledTaskForGantt): boolean =>
  task.status === 'DOWNTIME' || task.wo_id.startsWith('DT-')

const getTaskColor = (status?: string): string => {
  switch (status) {
    case 'RUNNING': return STATUS_COLORS.running
    case 'DONE': return STATUS_COLORS.completed
    case 'PAUSE': return STATUS_COLORS.paused
    case 'ERROR': return STATUS_COLORS.error
    case 'DOWNTIME': return STATUS_COLORS.downtime
    case 'SCHEDULED': return STATUS_COLORS.scheduled
    default: return STATUS_COLORS.scheduled // READY or undefined
  }
}

const getTaskStyle = (task: ScheduledTaskForGantt) => {
  const startMinutes = task.start_time / 60
  const durationMinutes = (task.end_time - task.start_time) / 60
  const left = (startMinutes / 60) * HOUR_WIDTH
  const width = Math.max((durationMinutes / 60) * HOUR_WIDTH, 40) // minimum 40px

  return {
    left: `${left}px`,
    width: `${width}px`,
  }
}

// Helper to create a task
function makeTask(overrides: Partial<ScheduledTaskForGantt> = {}): ScheduledTaskForGantt {
  return {
    wo_id: 'WO-1',
    job_id: 'LOT-001',
    op_id: 'OP-1',
    machine_id: 'CNC-001',
    start_time: 3600,   // 1 hour from horizon start
    end_time: 7200,     // 2 hours
    quantity: 10,
    status: 'READY',
    ...overrides,
  }
}

// --- Tests ---

describe('isDowntimeTask', () => {
  it('returns false for normal work order task', () => {
    expect(isDowntimeTask(makeTask({ wo_id: 'WO-42', status: 'RUNNING' }))).toBe(false)
  })

  it('returns true when status is DOWNTIME', () => {
    expect(isDowntimeTask(makeTask({ wo_id: 'WO-1', status: 'DOWNTIME' }))).toBe(true)
  })

  it('returns true when wo_id starts with DT-', () => {
    expect(isDowntimeTask(makeTask({ wo_id: 'DT-5', status: 'READY' }))).toBe(true)
  })

  it('returns true when both status is DOWNTIME and wo_id starts with DT-', () => {
    expect(isDowntimeTask(makeTask({ wo_id: 'DT-3', status: 'DOWNTIME' }))).toBe(true)
  })

  it('returns false when wo_id contains DT but does not start with DT-', () => {
    expect(isDowntimeTask(makeTask({ wo_id: 'WO-DT-1', status: 'READY' }))).toBe(false)
  })

  it('returns false for undefined status with normal wo_id', () => {
    const task = makeTask({ wo_id: 'WO-99' })
    delete task.status
    expect(isDowntimeTask(task)).toBe(false)
  })
})

describe('getTaskColor', () => {
  it('returns running colors for RUNNING status', () => {
    expect(getTaskColor('RUNNING')).toBe(STATUS_COLORS.running)
  })

  it('returns completed colors for DONE status', () => {
    expect(getTaskColor('DONE')).toBe(STATUS_COLORS.completed)
  })

  it('returns paused colors for PAUSE status', () => {
    expect(getTaskColor('PAUSE')).toBe(STATUS_COLORS.paused)
  })

  it('returns error colors for ERROR status', () => {
    expect(getTaskColor('ERROR')).toBe(STATUS_COLORS.error)
  })

  it('returns downtime colors for DOWNTIME status', () => {
    expect(getTaskColor('DOWNTIME')).toBe(STATUS_COLORS.downtime)
  })

  it('returns scheduled colors for SCHEDULED status', () => {
    expect(getTaskColor('SCHEDULED')).toBe(STATUS_COLORS.scheduled)
  })

  it('returns scheduled (default) colors for READY status', () => {
    expect(getTaskColor('READY')).toBe(STATUS_COLORS.scheduled)
  })

  it('returns scheduled (default) colors for undefined status', () => {
    expect(getTaskColor(undefined)).toBe(STATUS_COLORS.scheduled)
  })

  it('returns scheduled (default) colors for unknown status', () => {
    expect(getTaskColor('UNKNOWN_STATUS')).toBe(STATUS_COLORS.scheduled)
  })
})

describe('getTaskStyle', () => {
  it('calculates left position based on start_time', () => {
    // start_time = 3600s = 60min → 60min/60min * 60px = 60px
    const task = makeTask({ start_time: 3600, end_time: 7200 })
    const style = getTaskStyle(task)
    expect(style.left).toBe('60px')
  })

  it('calculates width based on duration', () => {
    // duration = 7200-3600 = 3600s = 60min → 60min/60 * 60px = 60px
    const task = makeTask({ start_time: 3600, end_time: 7200 })
    const style = getTaskStyle(task)
    expect(style.width).toBe('60px')
  })

  it('sets left to 0px when start_time is 0', () => {
    const task = makeTask({ start_time: 0, end_time: 1800 })
    const style = getTaskStyle(task)
    expect(style.left).toBe('0px')
  })

  it('applies minimum 40px width for very short tasks', () => {
    // duration = 60s = 1min → (1/60)*60 = 1px, but min is 40px
    const task = makeTask({ start_time: 0, end_time: 60 })
    const style = getTaskStyle(task)
    expect(style.width).toBe('40px')
  })

  it('applies minimum 40px width for zero-duration tasks', () => {
    const task = makeTask({ start_time: 3600, end_time: 3600 })
    const style = getTaskStyle(task)
    expect(style.width).toBe('40px')
  })

  it('returns correct pixel values for 2-hour task at 2-hour offset', () => {
    // start_time = 7200s = 2h → left = 120px
    // end_time = 14400s = 4h, duration = 7200s = 2h → width = 120px
    const task = makeTask({ start_time: 7200, end_time: 14400 })
    const style = getTaskStyle(task)
    expect(style.left).toBe('120px')
    expect(style.width).toBe('120px')
  })

  it('calculates width for a 30-minute task', () => {
    // 1800s = 30min → (30/60)*60 = 30px, but min is 40px
    const task = makeTask({ start_time: 0, end_time: 1800 })
    const style = getTaskStyle(task)
    expect(style.width).toBe('40px')
  })

  it('calculates width for a 90-minute task', () => {
    // 5400s = 90min → (90/60)*60 = 90px
    const task = makeTask({ start_time: 0, end_time: 5400 })
    const style = getTaskStyle(task)
    expect(style.width).toBe('90px')
  })
})

describe('downtime vs normal task counting', () => {
  const tasks: ScheduledTaskForGantt[] = [
    makeTask({ wo_id: 'WO-1', status: 'RUNNING' }),
    makeTask({ wo_id: 'WO-2', status: 'SCHEDULED' }),
    makeTask({ wo_id: 'DT-1', status: 'DOWNTIME' }),
    makeTask({ wo_id: 'DT-2', status: 'DOWNTIME' }),
  ]

  it('correctly counts normal tasks (non-downtime)', () => {
    const normalCount = tasks.filter(t => !isDowntimeTask(t)).length
    expect(normalCount).toBe(2)
  })

  it('correctly counts downtime tasks', () => {
    const downtimeCount = tasks.filter(t => isDowntimeTask(t)).length
    expect(downtimeCount).toBe(2)
  })

  it('total tasks = normal + downtime', () => {
    const normalCount = tasks.filter(t => !isDowntimeTask(t)).length
    const downtimeCount = tasks.filter(t => isDowntimeTask(t)).length
    expect(normalCount + downtimeCount).toBe(tasks.length)
  })
})

describe('ongoing downtime detection', () => {
  it('identifies ongoing downtime when end_time >= 86340 (23:59:00)', () => {
    const task = makeTask({ wo_id: 'DT-1', status: 'DOWNTIME', end_time: 86340 })
    const isOngoing = isDowntimeTask(task) && task.end_time >= 86340
    expect(isOngoing).toBe(true)
  })

  it('does not flag completed downtime with end_time < 86340 as ongoing', () => {
    const task = makeTask({ wo_id: 'DT-2', status: 'DOWNTIME', end_time: 7200 })
    const isOngoing = isDowntimeTask(task) && task.end_time >= 86340
    expect(isOngoing).toBe(false)
  })

  it('non-downtime task with end_time >= 86340 is not ongoing downtime', () => {
    const task = makeTask({ wo_id: 'WO-1', status: 'RUNNING', end_time: 86400 })
    const isOngoing = isDowntimeTask(task) && task.end_time >= 86340
    expect(isOngoing).toBe(false)
  })
})
