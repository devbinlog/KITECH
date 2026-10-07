'use client'

import { useEffect, useState } from 'react'
import { apiClient, ScheduleData, QualityMetrics, Statistics, GanttData } from '@/app/lib/api'
import { MetricsGrid } from '@/app/components/MetricsGrid'
import { GanttChart } from '@/app/components/GanttChart'
import { UtilizationChart } from '@/app/components/UtilizationChart'
import { LatenessChart } from '@/app/components/LatenessChart'

export default function Home() {
  const [schedule, setSchedule] = useState<ScheduleData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const loadSchedule = async () => {
      setLoading(true)
      setError(null)

      try {
        // Check API health first
        const isHealthy = await apiClient.health()
        if (!isHealthy) {
          setError('Unable to connect to API server')
          setConnected(false)
          return
        }

        setConnected(true)

        // Load full schedule data
        const data = await apiClient.getSchedule()
        if (data) {
          setSchedule(data)
        } else {
          setError('Failed to load schedule data')
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setError(`Error loading schedule: ${message}`)
        setConnected(false)
      } finally {
        setLoading(false)
      }
    }

    loadSchedule()
  }, [])

  return (
    <main className="min-h-screen bg-gradient-to-br from-primary to-secondary p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-4xl font-bold text-white">🏭 Manufacturing Schedule</h1>
            <div className="flex items-center gap-3">
              <div
                className={`w-3 h-3 rounded-full ${connected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}
              />
              <span className="text-white font-semibold">
                {connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
          <p className="text-white text-lg opacity-90">Interactive Visualization of Scheduled Tasks and Metrics</p>
        </div>

        {loading && (
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4" />
            <p className="text-gray-600">Loading schedule data...</p>
          </div>
        )}

        {error && !loading && (
          <div className="bg-red-50 border-l-4 border-red-500 rounded-lg shadow-lg p-6 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-500" viewBox="0 0 20 20" fill="currentColor">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-600">{error}</p>
                <p className="text-xs text-red-500 mt-2">Make sure the API server is running</p>
              </div>
            </div>
          </div>
        )}

        {!loading && schedule && !error && (
          <div className="space-y-6">
            <MetricsGrid
              metrics={schedule.quality_metrics}
              statistics={schedule.statistics}
            />

            <div className="grid grid-cols-1 gap-6">
              {schedule.gantt_data && schedule.gantt_data.tasks && schedule.gantt_data.tasks.length > 0 && (
                <GanttChart ganttData={schedule.gantt_data} />
              )}

              {schedule.quality_metrics.machine_utilization && (
                <UtilizationChart
                  data={schedule.quality_metrics.machine_utilization}
                  average={schedule.quality_metrics.avg_machine_utilization}
                />
              )}

              {schedule.quality_metrics.per_wo_lateness && (
                <LatenessChart
                  data={schedule.quality_metrics.per_wo_lateness}
                  total={schedule.quality_metrics.total_lateness_hours}
                />
              )}
            </div>

            <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg shadow-lg p-6 text-white text-center text-sm">
              <p>🚀 Manufacturing Intelligence System | Schedule Visualizer Frontend</p>
              <p className="mt-2 opacity-75">Last updated: {new Date().toLocaleString()}</p>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
