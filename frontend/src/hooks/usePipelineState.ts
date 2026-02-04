import { useState, useCallback, useMemo } from 'react'
import type { PipelineState, PipelineStep, WebSocketEvent, PipelineSummaryData } from '@/types'
import { createInitialPipelineState, PIPELINE_STEPS, isValidPipelineStep } from '@/types'

export interface UsePipelineStateReturn {
  state: PipelineState
  handleEvent: (event: WebSocketEvent) => void
  reset: () => void
  overallProgress: number
  completedSteps: number
}

export function usePipelineState(): UsePipelineStateReturn {
  const [state, setState] = useState<PipelineState>(createInitialPipelineState)

  const handleEvent = useCallback((event: WebSocketEvent) => {
    setState((prev) => {
      switch (event.type) {
        case 'connected':
          // Connection event - no state change needed
          return prev

        case 'pipeline_started':
          return {
            ...prev,
            status: 'running',
            runId: event.runId,
            startedAt: new Date().toISOString(),
            error: undefined, // Clear any previous error
            summary: undefined, // Clear any previous summary
          }

        case 'step_started': {
          // Validate step before updating
          if (!isValidPipelineStep(event.step)) {
            console.warn(`Invalid step received: ${event.step}`)
            return prev
          }
          const step = event.step as PipelineStep
          return {
            ...prev,
            currentStep: step,
            steps: {
              ...prev.steps,
              [step]: {
                ...prev.steps[step],
                status: 'running',
                startedAt: new Date().toISOString(),
                progress: 0,
                message: '',
                error: undefined, // Clear any previous step error
              },
            },
          }
        }

        case 'step_progress': {
          // Validate step before updating
          if (!isValidPipelineStep(event.step)) {
            console.warn(`Invalid step received: ${event.step}`)
            return prev
          }
          const step = event.step as PipelineStep
          return {
            ...prev,
            steps: {
              ...prev.steps,
              [step]: {
                ...prev.steps[step],
                progress: event.percentage,
                message: event.message,
              },
            },
          }
        }

        case 'step_completed': {
          // Validate step before updating
          if (!isValidPipelineStep(event.step)) {
            console.warn(`Invalid step received: ${event.step}`)
            return prev
          }
          const step = event.step as PipelineStep
          return {
            ...prev,
            steps: {
              ...prev.steps,
              [step]: {
                ...prev.steps[step],
                status: 'completed',
                progress: 100,
                completedAt: new Date().toISOString(),
                duration: event.duration,
                itemsProcessed: event.itemsProcessed,
              },
            },
          }
        }

        case 'step_failed': {
          // Validate step before updating
          if (!isValidPipelineStep(event.step)) {
            console.warn(`Invalid step received: ${event.step}`)
            return prev
          }
          const step = event.step as PipelineStep
          return {
            ...prev,
            steps: {
              ...prev.steps,
              [step]: {
                ...prev.steps[step],
                status: 'failed',
                error: event.error,
              },
            },
          }
        }

        case 'pipeline_completed': {
          // Store the summary data
          const summaryData: PipelineSummaryData = {
            totalDuration: event.summary.totalDuration,
            stepsCompleted: event.summary.stepsCompleted,
            totalSteps: event.summary.totalSteps,
            sitesProcessed: event.summary.sitesProcessed,
          }
          return {
            ...prev,
            status: 'completed',
            currentStep: null,
            completedAt: new Date().toISOString(),
            summary: summaryData,
          }
        }

        case 'pipeline_failed':
          return {
            ...prev,
            status: 'failed',
            currentStep: null,
            error: event.error,
          }

        default:
          // Unknown event type - ignore gracefully
          return prev
      }
    })
  }, [])

  const reset = useCallback(() => {
    setState(createInitialPipelineState())
  }, [])

  const completedSteps = useMemo(() => {
    return PIPELINE_STEPS.filter(
      (step) => state.steps[step].status === 'completed'
    ).length
  }, [state.steps])

  // Calculate overall progress including partial step progress
  const overallProgress = useMemo(() => {
    const baseProgress = (completedSteps / PIPELINE_STEPS.length) * 100

    // Add partial progress from currently running step
    if (state.currentStep && state.steps[state.currentStep].status === 'running') {
      const stepWeight = 100 / PIPELINE_STEPS.length
      const stepProgress = state.steps[state.currentStep].progress / 100
      return baseProgress + (stepWeight * stepProgress)
    }

    return baseProgress
  }, [completedSteps, state.currentStep, state.steps])

  return {
    state,
    handleEvent,
    reset,
    overallProgress,
    completedSteps,
  }
}
