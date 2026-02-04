import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { usePipelineState } from './usePipelineState'

describe('usePipelineState', () => {
  beforeEach(() => {
    vi.spyOn(console, 'warn').mockImplementation(() => {})
  })

  describe('initial state', () => {
    it('returns idle state initially', () => {
      const { result } = renderHook(() => usePipelineState())

      expect(result.current.state.status).toBe('idle')
      expect(result.current.state.currentStep).toBeNull()
    })

    it('has all steps initialized as idle', () => {
      const { result } = renderHook(() => usePipelineState())

      const steps = result.current.state.steps
      expect(steps.discovery.status).toBe('idle')
      expect(steps.verification.status).toBe('idle')
      expect(steps.audit.status).toBe('idle')
      expect(steps.analysis.status).toBe('idle')
      expect(steps.contacts.status).toBe('idle')
      expect(steps.outreach.status).toBe('idle')
    })
  })

  describe('handleEvent', () => {
    it('handles connected event without state change', () => {
      const { result } = renderHook(() => usePipelineState())

      act(() => {
        result.current.handleEvent({
          type: 'connected',
          clientId: 'test-123',
        })
      })

      expect(result.current.state.status).toBe('idle')
      expect(result.current.state.currentStep).toBeNull()
    })

    it('handles pipeline_started event', () => {
      const { result } = renderHook(() => usePipelineState())

      act(() => {
        result.current.handleEvent({
          type: 'pipeline_started',
          runId: 'run-123',
          steps: ['discovery', 'verification'],
        })
      })

      expect(result.current.state.status).toBe('running')
      expect(result.current.state.runId).toBe('run-123')
    })

    it('handles step_started event', () => {
      const { result } = renderHook(() => usePipelineState())

      act(() => {
        result.current.handleEvent({
          type: 'step_started',
          step: 'discovery',
        })
      })

      expect(result.current.state.currentStep).toBe('discovery')
      expect(result.current.state.steps.discovery.status).toBe('running')
    })

    it('handles step_progress event', () => {
      const { result } = renderHook(() => usePipelineState())

      act(() => {
        result.current.handleEvent({
          type: 'step_started',
          step: 'discovery',
        })
      })

      act(() => {
        result.current.handleEvent({
          type: 'step_progress',
          step: 'discovery',
          current: 5,
          total: 10,
          percentage: 50,
          message: 'Processing...',
        })
      })

      expect(result.current.state.steps.discovery.progress).toBe(50)
      expect(result.current.state.steps.discovery.message).toBe('Processing...')
    })

    it('handles step_completed event', () => {
      const { result } = renderHook(() => usePipelineState())

      act(() => {
        result.current.handleEvent({
          type: 'step_started',
          step: 'discovery',
        })
      })

      act(() => {
        result.current.handleEvent({
          type: 'step_completed',
          step: 'discovery',
          duration: 5000,
          itemsProcessed: 10,
        })
      })

      expect(result.current.state.steps.discovery.status).toBe('completed')
      expect(result.current.state.steps.discovery.duration).toBe(5000)
      expect(result.current.state.steps.discovery.itemsProcessed).toBe(10)
    })

    it('handles step_failed event', () => {
      const { result } = renderHook(() => usePipelineState())

      act(() => {
        result.current.handleEvent({
          type: 'step_started',
          step: 'discovery',
        })
      })

      act(() => {
        result.current.handleEvent({
          type: 'step_failed',
          step: 'discovery',
          error: 'Connection timeout',
        })
      })

      expect(result.current.state.steps.discovery.status).toBe('failed')
      expect(result.current.state.steps.discovery.error).toBe('Connection timeout')
    })

    it('handles pipeline_completed event and stores summary', () => {
      const { result } = renderHook(() => usePipelineState())

      act(() => {
        result.current.handleEvent({
          type: 'pipeline_started',
          runId: 'run-123',
          steps: ['discovery'],
        })
      })

      act(() => {
        result.current.handleEvent({
          type: 'pipeline_completed',
          summary: {
            totalDuration: 60000,
            stepsCompleted: 6,
            totalSteps: 6,
            sitesProcessed: 5,
          },
        })
      })

      expect(result.current.state.status).toBe('completed')
      expect(result.current.state.summary).toEqual({
        totalDuration: 60000,
        stepsCompleted: 6,
        totalSteps: 6,
        sitesProcessed: 5,
      })
    })

    it('handles pipeline_failed event and stores error', () => {
      const { result } = renderHook(() => usePipelineState())

      act(() => {
        result.current.handleEvent({
          type: 'pipeline_started',
          runId: 'run-123',
          steps: ['discovery'],
        })
      })

      act(() => {
        result.current.handleEvent({
          type: 'pipeline_failed',
          error: 'Fatal error occurred',
        })
      })

      expect(result.current.state.status).toBe('failed')
      expect(result.current.state.error).toBe('Fatal error occurred')
    })

    it('ignores unknown event types gracefully', () => {
      const { result } = renderHook(() => usePipelineState())

      const initialState = { ...result.current.state }

      act(() => {
        // Cast to unknown to test runtime behavior with invalid event
        result.current.handleEvent({
          type: 'unknown_event',
          data: 'test',
        } as unknown as Parameters<typeof result.current.handleEvent>[0])
      })

      expect(result.current.state.status).toBe(initialState.status)
    })

    it('validates step names and ignores invalid steps', () => {
      const { result } = renderHook(() => usePipelineState())

      act(() => {
        result.current.handleEvent({
          type: 'step_started',
          step: 'invalid_step',
        })
      })

      expect(result.current.state.currentStep).toBeNull()
      expect(console.warn).toHaveBeenCalledWith('Invalid step received: invalid_step')
    })

    it('clears previous error and summary when pipeline starts', () => {
      const { result } = renderHook(() => usePipelineState())

      // First run that fails
      act(() => {
        result.current.handleEvent({
          type: 'pipeline_started',
          runId: 'run-1',
          steps: ['discovery'],
        })
        result.current.handleEvent({
          type: 'pipeline_failed',
          error: 'Previous error',
        })
      })

      expect(result.current.state.error).toBe('Previous error')

      // Second run should clear error
      act(() => {
        result.current.handleEvent({
          type: 'pipeline_started',
          runId: 'run-2',
          steps: ['discovery'],
        })
      })

      expect(result.current.state.error).toBeUndefined()
      expect(result.current.state.summary).toBeUndefined()
    })
  })

  describe('reset', () => {
    it('resets state to initial values', () => {
      const { result } = renderHook(() => usePipelineState())

      act(() => {
        result.current.handleEvent({
          type: 'pipeline_started',
          runId: 'run-123',
          steps: ['discovery'],
        })
      })

      expect(result.current.state.status).toBe('running')

      act(() => {
        result.current.reset()
      })

      expect(result.current.state.status).toBe('idle')
      expect(result.current.state.currentStep).toBeNull()
      expect(result.current.state.runId).toBeUndefined()
    })
  })

  describe('computed values', () => {
    it('calculates overall progress with completed steps only', () => {
      const { result } = renderHook(() => usePipelineState())

      act(() => {
        result.current.handleEvent({ type: 'step_started', step: 'discovery' })
        result.current.handleEvent({
          type: 'step_completed',
          step: 'discovery',
          duration: 1000,
          itemsProcessed: 5,
        })
        result.current.handleEvent({ type: 'step_started', step: 'verification' })
        result.current.handleEvent({
          type: 'step_completed',
          step: 'verification',
          duration: 2000,
          itemsProcessed: 3,
        })
      })

      // 2 of 6 steps completed = ~33%
      expect(result.current.overallProgress).toBeCloseTo(33.33, 0)
    })

    it('includes partial progress from running step', () => {
      const { result } = renderHook(() => usePipelineState())

      act(() => {
        result.current.handleEvent({ type: 'step_started', step: 'discovery' })
        result.current.handleEvent({
          type: 'step_progress',
          step: 'discovery',
          current: 5,
          total: 10,
          percentage: 50,
          message: 'Processing...',
        })
      })

      // 0 completed steps + 50% of 1 step = 50% of (100/6) = ~8.33%
      expect(result.current.overallProgress).toBeCloseTo(8.33, 0)
    })

    it('returns completed steps count', () => {
      const { result } = renderHook(() => usePipelineState())

      expect(result.current.completedSteps).toBe(0)

      act(() => {
        result.current.handleEvent({ type: 'step_started', step: 'discovery' })
        result.current.handleEvent({
          type: 'step_completed',
          step: 'discovery',
          duration: 1000,
          itemsProcessed: 5,
        })
      })

      expect(result.current.completedSteps).toBe(1)
    })
  })
})
