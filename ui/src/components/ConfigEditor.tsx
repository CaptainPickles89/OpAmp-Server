import { useEffect, useRef } from 'react'
import { EditorState } from '@codemirror/state'
import { EditorView, lineNumbers, highlightActiveLineGutter, keymap } from '@codemirror/view'
import { yaml } from '@codemirror/lang-yaml'
import { oneDark } from '@codemirror/theme-one-dark'
import { indentWithTab } from '@codemirror/commands'

interface ConfigEditorProps {
  value: string
  onChange?: (value: string) => void
  readOnly?: boolean
}

const editorTheme = EditorView.theme({
  '&': {
    backgroundColor: '#0E1223',
    fontFamily: 'ui-monospace, Consolas, "Courier New", monospace',
    minHeight: '300px',
  },
  '.cm-scroller': {
    fontFamily: 'ui-monospace, Consolas, "Courier New", monospace',
  },
})

export function ConfigEditor({ value, onChange, readOnly = false }: ConfigEditorProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const viewRef = useRef<EditorView | null>(null)

  useEffect(() => {
    if (!containerRef.current) return

    const extensions = [
      yaml(),
      oneDark,
      editorTheme,
      lineNumbers(),
      highlightActiveLineGutter(),
      keymap.of([indentWithTab]),
      EditorState.readOnly.of(readOnly),
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
    // Only create editor once on mount — value updates handled separately
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [readOnly])

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
      className="min-h-[300px] rounded-md border border-slate-700 overflow-hidden font-mono"
      data-testid="config-editor"
      aria-label="YAML configuration editor"
      aria-readonly={readOnly}
    />
  )
}
