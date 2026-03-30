/**
 * TDD RED stubs for ColumnPicker component (COLS-04, COLS-05).
 * All tests fail because @/components/ColumnPicker does not exist yet.
 */
import { screen, fireEvent } from '@testing-library/react'
import { renderWithProviders } from '@/test/renderWithProviders'
import { ColumnPicker } from '@/components/ColumnPicker'

describe('ColumnPicker', () => {
  const defaultProps = {
    allKeys: ['host.name', 'os.type'],
    enabledKeys: ['host.name'],
    onToggle: vi.fn(),
  }

  beforeEach(() => {
    defaultProps.onToggle.mockClear()
  })

  it('renders trigger button with "Columns" label', () => {
    renderWithProviders(<ColumnPicker {...defaultProps} />)
    expect(screen.getByRole('button', { name: /columns/i })).toBeInTheDocument()
  })

  it('opens popover on click showing attribute keys', () => {
    renderWithProviders(<ColumnPicker {...defaultProps} />)
    fireEvent.click(screen.getByRole('button', { name: /columns/i }))
    expect(screen.getByLabelText('host.name')).toBeInTheDocument()
    expect(screen.getByLabelText('os.type')).toBeInTheDocument()
  })

  it('checked state reflects enabledKeys', () => {
    renderWithProviders(
      <ColumnPicker
        allKeys={['host.name', 'os.type']}
        enabledKeys={['host.name']}
        onToggle={vi.fn()}
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: /columns/i }))
    expect(screen.getByLabelText('host.name')).toBeChecked()
    expect(screen.getByLabelText('os.type')).not.toBeChecked()
  })

  it('calls onToggle on checkbox change', () => {
    const onToggle = vi.fn()
    renderWithProviders(
      <ColumnPicker
        allKeys={['host.name', 'os.type']}
        enabledKeys={['host.name']}
        onToggle={onToggle}
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: /columns/i }))
    fireEvent.click(screen.getByLabelText('os.type'))
    expect(onToggle).toHaveBeenCalledWith('os.type')
  })

  it('closes on outside click', () => {
    renderWithProviders(<ColumnPicker {...defaultProps} />)
    fireEvent.click(screen.getByRole('button', { name: /columns/i }))
    expect(screen.getByLabelText('host.name')).toBeInTheDocument()
    fireEvent.mouseDown(document.body)
    expect(screen.queryByLabelText('host.name')).not.toBeInTheDocument()
  })
})
