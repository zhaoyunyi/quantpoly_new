import { describe, it, expect, vi } from 'vitest'
import { exportCsv } from '../../app/shared/exportCsv'

describe('exportCsv', () => {
  it('given_data_when_export_then_creates_download_link', () => {
    const createObjectURL = vi.fn(() => 'blob:test')
    const revokeObjectURL = vi.fn()
    vi.stubGlobal('URL', { createObjectURL, revokeObjectURL })

    const clickMock = vi.fn()
    vi.spyOn(document, 'createElement').mockReturnValue({
      click: clickMock,
      set href(v: string) {},
      set download(v: string) {},
    } as unknown as HTMLAnchorElement)

    exportCsv('test.csv', ['Name', 'Value'], [['foo', '123'], ['bar', '456']])

    expect(createObjectURL).toHaveBeenCalledOnce()
    expect(clickMock).toHaveBeenCalledOnce()
    expect(revokeObjectURL).toHaveBeenCalledOnce()
  })

  it('given_cell_with_comma_when_export_then_escapes_with_quotes', () => {
    const blobs: Blob[] = []
    const createObjectURL = vi.fn((blob: Blob) => {
      blobs.push(blob)
      return 'blob:test'
    })
    const revokeObjectURL = vi.fn()
    vi.stubGlobal('URL', { createObjectURL, revokeObjectURL })

    vi.spyOn(document, 'createElement').mockReturnValue({
      click: vi.fn(),
      set href(v: string) {},
      set download(v: string) {},
    } as unknown as HTMLAnchorElement)

    exportCsv('test.csv', ['Name'], [['hello, world']])

    expect(blobs.length).toBe(1)
  })

  it('given_thousand_separated_number_when_export_then_quotes_the_cell', async () => {
    class BlobMock {
      constructor(public readonly parts: unknown[]) {}
    }

    const blobs: BlobMock[] = []
    const createObjectURL = vi.fn((blob: BlobMock) => {
      blobs.push(blob)
      return 'blob:test'
    })
    const revokeObjectURL = vi.fn()
    vi.stubGlobal('Blob', BlobMock as unknown as typeof Blob)
    vi.stubGlobal('URL', { createObjectURL, revokeObjectURL })

    vi.spyOn(document, 'createElement').mockReturnValue({
      click: vi.fn(),
      set href(v: string) {},
      set download(v: string) {},
    } as unknown as HTMLAnchorElement)

    exportCsv('test.csv', ['Value'], [['1,234.5']])

    expect(blobs).toHaveLength(1)
    expect(String(blobs[0].parts[0])).toContain('"1,234.5"')
  })
})
