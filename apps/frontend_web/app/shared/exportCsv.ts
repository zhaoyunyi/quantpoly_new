export function exportCsv(filename: string, headers: string[], rows: string[][]) {
  const csvContent = [
    headers.join(','),
    ...rows.map((row) =>
      row.map((cell) => {
        const escaped = String(cell).replace(/"/g, '""')
        return /[,"\n]/.test(escaped) ? `"${escaped}"` : escaped
      }).join(',')
    ),
  ].join('\n')

  const blob = new Blob(['\uFEFF' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
