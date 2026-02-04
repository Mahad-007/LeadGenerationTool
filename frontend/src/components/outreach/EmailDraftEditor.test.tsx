import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { EmailDraftEditor, type EmailDraftEditorProps } from './EmailDraftEditor'
import type { EmailDraft } from '@/types'

const mockDraft: EmailDraft = {
  store_url: 'https://example-store.com',
  subject: 'Mobile experience feedback for Example Store',
  body: `Hi there,

I recently visited Example Store on my mobile device and noticed an issue that might be affecting your mobile shoppers.

The mobile navigation menu appears to be difficult to access, which could be impacting user experience.

Would you be open to a quick chat about some improvements?

Best regards`,
  to_emails: ['contact@example-store.com'],
  social: {
    instagram: 'https://instagram.com/examplestore',
    facebook: 'https://facebook.com/examplestore',
  },
  issue_referenced: {
    title: 'Mobile Navigation Issue',
    category: 'mobile',
    severity: 'high',
  },
}

function renderEmailDraftEditor(props: Partial<EmailDraftEditorProps> = {}) {
  const defaultProps: EmailDraftEditorProps = {
    draft: mockDraft,
    onSave: () => {},
    onCopy: () => {},
    ...props,
  }

  return render(<EmailDraftEditor {...defaultProps} />)
}

describe('EmailDraftEditor', () => {
  describe('rendering', () => {
    it('renders the store URL in header', () => {
      renderEmailDraftEditor()
      expect(screen.getByText('example-store.com')).toBeInTheDocument()
    })

    it('renders the subject line', () => {
      renderEmailDraftEditor()
      const subjectInput = screen.getByLabelText(/subject/i)
      expect(subjectInput).toHaveValue('Mobile experience feedback for Example Store')
    })

    it('renders the email body', () => {
      renderEmailDraftEditor()
      const bodyInput = screen.getByLabelText(/body/i)
      expect(bodyInput.textContent).toContain('mobile shoppers')
    })

    it('shows recipient emails', () => {
      renderEmailDraftEditor()
      expect(screen.getByText('contact@example-store.com')).toBeInTheDocument()
    })

    it('shows social links when no email available', () => {
      const draftWithNoEmail = {
        ...mockDraft,
        to_emails: [],
      }
      renderEmailDraftEditor({ draft: draftWithNoEmail })
      expect(screen.getByText(/instagram/i)).toBeInTheDocument()
    })
  })

  describe('editing', () => {
    it('allows editing the subject', async () => {
      const user = userEvent.setup()
      renderEmailDraftEditor()

      const subjectInput = screen.getByLabelText(/subject/i)
      await user.clear(subjectInput)
      await user.type(subjectInput, 'New subject')

      expect(subjectInput).toHaveValue('New subject')
    })

    it('allows editing the body', async () => {
      const user = userEvent.setup()
      renderEmailDraftEditor()

      const bodyInput = screen.getByLabelText(/body/i)
      await user.clear(bodyInput)
      await user.type(bodyInput, 'New body content')

      expect(bodyInput).toHaveValue('New body content')
    })
  })

  describe('actions', () => {
    it('calls onSave when save button is clicked', async () => {
      const user = userEvent.setup()
      const onSave = vi.fn()
      renderEmailDraftEditor({ onSave })

      await user.click(screen.getByRole('button', { name: /save/i }))

      expect(onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          store_url: 'https://example-store.com',
          subject: 'Mobile experience feedback for Example Store',
        })
      )
    })

    it('calls onCopy when copy button is clicked', async () => {
      const user = userEvent.setup()
      const onCopy = vi.fn()
      renderEmailDraftEditor({ onCopy })

      await user.click(screen.getByRole('button', { name: /copy/i }))

      expect(onCopy).toHaveBeenCalledWith(
        expect.objectContaining({
          subject: 'Mobile experience feedback for Example Store',
        })
      )
    })

    it('calls onSave with edited content', async () => {
      const user = userEvent.setup()
      const onSave = vi.fn()
      renderEmailDraftEditor({ onSave })

      const subjectInput = screen.getByLabelText(/subject/i)
      await user.clear(subjectInput)
      await user.type(subjectInput, 'Edited subject')

      await user.click(screen.getByRole('button', { name: /save/i }))

      expect(onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          subject: 'Edited subject',
        })
      )
    })

    it('resets to original content when reset is clicked', async () => {
      const user = userEvent.setup()
      renderEmailDraftEditor()

      const subjectInput = screen.getByLabelText(/subject/i)
      await user.clear(subjectInput)
      await user.type(subjectInput, 'Edited subject')

      await user.click(screen.getByRole('button', { name: /reset/i }))

      expect(subjectInput).toHaveValue('Mobile experience feedback for Example Store')
    })
  })

  describe('issue reference', () => {
    it('displays the referenced issue', () => {
      renderEmailDraftEditor()
      expect(screen.getByText('Mobile Navigation Issue')).toBeInTheDocument()
    })

    it('displays issue severity', () => {
      renderEmailDraftEditor()
      expect(screen.getByText(/high/i)).toBeInTheDocument()
    })

    it('displays issue category', () => {
      renderEmailDraftEditor()
      // Use exact match for the category badge
      const categoryBadge = screen.getByText('mobile')
      expect(categoryBadge).toBeInTheDocument()
      expect(categoryBadge).toHaveClass('bg-gray-200')
    })
  })

  describe('accessibility', () => {
    it('has accessible form', () => {
      renderEmailDraftEditor()
      expect(screen.getByRole('form')).toBeInTheDocument()
    })

    it('has labeled inputs', () => {
      renderEmailDraftEditor()
      expect(screen.getByLabelText(/subject/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/body/i)).toBeInTheDocument()
    })
  })
})
