// Contacts Types - Based on /contacts/contacts.json

export interface ContactsMetadata {
  generated_at: string
  total_sites: number
  sites_with_contacts: number
  total_emails_found: number
  total_social_found: number
}

export interface SocialLinks {
  instagram?: string
  facebook?: string
  twitter?: string
  linkedin?: string
  tiktok?: string
  youtube?: string
  pinterest?: string
  snapchat?: string
}

export interface Contact {
  url: string
  extracted_at: string
  emails: string[]
  phones: string[]
  social: SocialLinks
  contact_page_found: boolean
  sources: string[]
  error: string | null
}

export interface ContactsResponse {
  metadata: ContactsMetadata
  contacts: Contact[]
}
