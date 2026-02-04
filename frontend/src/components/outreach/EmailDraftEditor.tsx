import { useState, useEffect } from 'react'
import { cn } from '@/lib/utils'
import type { EmailDraft } from '@/types'

export interface EmailDraftEditorProps {
  draft: EmailDraft
  onSave: (draft: EmailDraft) => void
  onCopy: (draft: EmailDraft) => void
}

function extractDomain(url: string): string {
  try {
    return new URL(url).hostname
  } catch {
    return url
  }
}

function getSeverityColor(severity: string): string {
  switch (severity) {
    case 'high':
      return 'bg-red-100 text-red-700'
    case 'medium':
      return 'bg-yellow-100 text-yellow-700'
    case 'low':
      return 'bg-green-100 text-green-700'
    default:
      return 'bg-gray-100 text-gray-700'
  }
}

export function EmailDraftEditor({
  draft,
  onSave,
  onCopy,
}: EmailDraftEditorProps) {
  const [subject, setSubject] = useState(draft.subject)
  const [body, setBody] = useState(draft.body)

  // Reset form when draft changes
  useEffect(() => {
    setSubject(draft.subject)
    setBody(draft.body)
  }, [draft])

  const handleSave = () => {
    onSave({
      ...draft,
      subject,
      body,
    })
  }

  const handleCopy = () => {
    onCopy({
      ...draft,
      subject,
      body,
    })
  }

  const handleReset = () => {
    setSubject(draft.subject)
    setBody(draft.body)
  }

  const hasEmails = draft.to_emails.length > 0
  const hasSocial = Object.keys(draft.social).some(
    (key) => draft.social[key as keyof typeof draft.social]
  )

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-900">
          {extractDomain(draft.store_url)}
        </h3>
        <span
          className={cn(
            'px-2 py-0.5 text-xs font-medium rounded-full capitalize',
            getSeverityColor(draft.issue_referenced.severity)
          )}
        >
          {draft.issue_referenced.severity}
        </span>
      </div>

      {/* Issue Reference */}
      <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">
          Referenced Issue
        </p>
        <p className="text-sm font-medium text-gray-900">
          {draft.issue_referenced.title}
        </p>
        <span className="inline-block mt-1 px-2 py-0.5 text-xs bg-gray-200 text-gray-700 rounded capitalize">
          {draft.issue_referenced.category}
        </span>
      </div>

      {/* Recipients */}
      <div className="px-4 py-3 border-b border-gray-200">
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">To</p>
        {hasEmails ? (
          <div className="flex flex-wrap gap-2">
            {draft.to_emails.map((email) => (
              <span
                key={email}
                className="px-2 py-1 text-sm bg-blue-50 text-blue-700 rounded"
              >
                {email}
              </span>
            ))}
          </div>
        ) : hasSocial ? (
          <div className="space-y-1">
            <p className="text-sm text-gray-500 italic mb-2">
              No email found. Contact via social:
            </p>
            <div className="flex flex-wrap gap-2">
              {draft.social.instagram && (
                <a
                  href={draft.social.instagram}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-2 py-1 text-sm bg-pink-50 text-pink-700 rounded hover:bg-pink-100"
                >
                  Instagram
                </a>
              )}
              {draft.social.facebook && (
                <a
                  href={draft.social.facebook}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-2 py-1 text-sm bg-blue-50 text-blue-700 rounded hover:bg-blue-100"
                >
                  Facebook
                </a>
              )}
              {draft.social.twitter && (
                <a
                  href={draft.social.twitter}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-2 py-1 text-sm bg-sky-50 text-sky-700 rounded hover:bg-sky-100"
                >
                  Twitter
                </a>
              )}
              {draft.social.linkedin && (
                <a
                  href={draft.social.linkedin}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-2 py-1 text-sm bg-blue-50 text-blue-800 rounded hover:bg-blue-100"
                >
                  LinkedIn
                </a>
              )}
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-500 italic">No contact information found</p>
        )}
      </div>

      {/* Form */}
      <form
        aria-label="Email draft editor"
        onSubmit={(e) => {
          e.preventDefault()
          handleSave()
        }}
        className="p-4 space-y-4"
      >
        {/* Subject */}
        <div>
          <label
            htmlFor="subject"
            className="block text-xs text-gray-500 uppercase tracking-wider mb-1"
          >
            Subject
          </label>
          <input
            id="subject"
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className={cn(
              'w-full px-3 py-2 border border-gray-300 rounded-md text-sm',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            )}
          />
        </div>

        {/* Body */}
        <div>
          <label
            htmlFor="body"
            className="block text-xs text-gray-500 uppercase tracking-wider mb-1"
          >
            Body
          </label>
          <textarea
            id="body"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={10}
            className={cn(
              'w-full px-3 py-2 border border-gray-300 rounded-md text-sm font-mono',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
              'resize-y min-h-[200px]'
            )}
          />
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-2">
          <button
            type="button"
            onClick={handleReset}
            className={cn(
              'px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900',
              'focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2'
            )}
          >
            Reset
          </button>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCopy}
              className={cn(
                'px-4 py-2 text-sm font-medium rounded-md transition-colors',
                'bg-gray-100 text-gray-700 hover:bg-gray-200',
                'focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2'
              )}
            >
              Copy to Clipboard
            </button>
            <button
              type="submit"
              className={cn(
                'px-4 py-2 text-sm font-medium rounded-md transition-colors',
                'bg-blue-600 text-white hover:bg-blue-700',
                'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
              )}
            >
              Save Changes
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
