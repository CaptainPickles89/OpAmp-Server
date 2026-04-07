import { useEffect, useRef } from 'react'
import { EditorState } from '@codemirror/state'
import { EditorView, lineNumbers, highlightActiveLineGutter, keymap } from '@codemirror/view'
import { yaml } from '@codemirror/lang-yaml'
import { oneDark } from '@codemirror/theme-one-dark'
import { indentWithTab } from '@codemirror/commands'
import { useTheme } from '@/hooks/useTheme'

interface ConfigEditorProps {
  value: string
  onChange?: (value: string) => void
  readOnly?: boolean
}

const darkEditorTheme = EditorView.theme({
  '&': {
    backgroundColor: '#0a1025',
    fontFamily: 'ui-monospace, Consolas, "Courier New", monospace',
    minHeight: '300px',
  },
  '.cm-scroller': {
    fontFamily: 'ui-monospace, Consolas, "Courier New", monospace',
  },
})

const lightEditorTheme = EditorView.theme({
  '&': {
    backgroundColor: '#f8faff',
    color: '#1e2642',
    fontFamily: 'ui-monospace, Consolas, "Courier New", monospace',
    minHeight: '300px',
  },
  '.cm-scroller': {
    fontFamily: 'ui-monospace, Consolas, "Courier New", monospace',
  },
  '.cm-gutters': {
    backgroundColor: '#f0f3fd',
    borderRight: '1px solid #dde3f0',
    color: '#8892b0',
  },
  '.cm-activeLineGutter': {
    backgroundColor: '#e8edfb',
  },
  '.cm-activeLine': {
    backgroundColor: 'rgba(66, 92, 199, 0.04)',
  },
  '.cm-selectionBackground, ::selection': {
    backgroundColor: '#b8c5e8 !important',
  },
  '.cm-cursor': {
    borderLeftColor: '#425CC7',
  },
})

export function ConfigEditor({ value, onChange, readOnly = false }: ConfigEditorProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const viewRef = useRef<EditorView | null>(null)
  const { theme } = useTheme()

  useEffect(() => {
    if (!containerRef.current) return

    const themeExtensions =
      theme === 'dark'
        ? [oneDark, darkEditorTheme]
        : [lightEditorTheme]

    const extensions = [
      yaml(),
      ...themeExtensions,
      lineNumbers(),
      highlightActiveLineGutter(),
      keymap.of([indentWithTab]),
      EditorState.readOnly.of(readOnly),
      EditorView.lineWrapping,
    ]

    if (onChange && !readOnly) {
      extensions.push(
        EditorView.updateListener.of(update => {
          if (update.docChanged) {
            onChange(update.state.doc.toString())
          }
        }),
      )
    }

    const state = EditorState.create({
      doc: value,
      extensions,
    })

    const view = new EditorView({
      state,
      parent: containerRef.current,
    })

    viewRef.current = view

    return () => {
      view.destroy()
      viewRef.current = null
    }
    // Recreate editor when readOnly or theme changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [readOnly, theme])

  // Update editor content when value prop changes (without re-creating the editor)
  useEffect(() => {
    const view = viewRef.current
    if (!view) return
    const current = view.state.doc.toString()
    if (current !== value) {
      view.dispatch({
        changes: { from: 0, to: current.length, insert: value },
      })
    }
  }, [value])

  return (
    <div
      ref={containerRef}
      className="min-h-[300px] rounded-md border border-border overflow-hidden font-mono"
      data-testid="config-editor"
      aria-label="YAML configuration editor"
      aria-readonly={readOnly}
    />
  )
}
