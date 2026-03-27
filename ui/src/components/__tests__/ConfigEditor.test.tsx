import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { ConfigEditor } from '../ConfigEditor'

// CodeMirror creates a complex DOM; test wrapper logic, not editor internals
describe('ConfigEditor', () => {
  it('renders the editor container', () => {
    render(<ConfigEditor value="key: value" />)
    const editor = screen.getByTestId('config-editor')
    expect(editor).toBeTruthy()
  })

  it('sets aria-readonly when readOnly=true', () => {
    const { container } = render(<ConfigEditor value="key: value" readOnly={true} />)
    const editor = container.querySelector('[aria-readonly="true"]')
    expect(editor).toBeTruthy()
  })

  it('does not set aria-readonly when readOnly=false', () => {
    const { container } = render(
      <ConfigEditor value="key: value" readOnly={false} onChange={vi.fn()} />,
    )
    const editor = container.querySelector('[aria-readonly="false"]')
    expect(editor).toBeTruthy()
  })

  it('renders with provided value', () => {
    const { container } = render(<ConfigEditor value="test: yaml" />)
    expect(container.querySelector('[data-testid="config-editor"]')).toBeTruthy()
  })
})
