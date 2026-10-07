'use client'

import { useMemo } from 'react'
import { GanttData } from '@/app/lib/api'

interface GanttChartProps {
  ganttData: GanttData
}

export function GanttChart({ ganttData }: GanttChartProps) {
  const chartData = useMemo(() => {
    return ganttData.tasks.map((task) => {
      const startTime = new Date(task.start).getTime()
      const endTime = new Date(task.end).getTime()
      const duration = (endTime - startTime) / (1000 * 60) // minutes

      return {
        name: task.name,
        resource: task.resource,
        start: startTime,
        duration,
        end: endTime,
        quantity: task.quantity,
        priority: task.priority,
      }
    })
  }, [ganttData])

  const machines = ganttData.resources || []

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">📊 Gantt Chart</h2>
      <div className="bg-gray-50 p-4 rounded border border-gray-200">
        <div className="overflow-x-auto">
          <div className="min-w-full">
            <div className="flex items-center mb-4">
              <div className="text-sm text-gray-600">
                {ganttData.tasks.length} tasks across {machines.length} machines
              </div>
            </div>
            
            <div className="space-y-2">
              {machines.map((machine) => {
                const machineTasks = chartData.filter((t) => t.resource === machine)
                const minStart = Math.min(...machineTasks.map((t) => t.start))
                const maxEnd = Math.max(...machineTasks.map((t) => t.end))
                const timelineLength = maxEnd - minStart

                return (
                  <div key={machine} className="border-b border-gray-200 pb-4">
                    <div className="font-semibold text-gray-700 mb-2">{machine}</div>
                    <div className="flex gap-2 overflow-x-auto">
                      {machineTasks.map((task, taskIdx) => {
                        const percentWidth = (task.duration * 60 * 1000 / timelineLength) * 100

                        const priorityColors = {
                          1: 'bg-red-400',
                          2: 'bg-orange-400',
                          3: 'bg-yellow-400',
                          default: 'bg-blue-400',
                        }
                        const color =
                          priorityColors[task.priority as keyof typeof priorityColors] ||
                          priorityColors.default

                        return (
                          <div
                            key={taskIdx}
                            className={`${color} text-white text-xs p-2 rounded cursor-pointer hover:opacity-80 transition-opacity whitespace-nowrap`}
                            style={{
                              minWidth: `max(100px, ${percentWidth}%)`,
                            }}
                            title={`${task.name}\nQty: ${task.quantity}\nDuration: ${task.duration.toFixed(0)}min`}
                          >
                            <div className="font-semibold truncate">{task.name}</div>
                            <div>Qty: {task.quantity}</div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
