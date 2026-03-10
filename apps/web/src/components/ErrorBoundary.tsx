import { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary:', error, info)
  }

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) return this.props.fallback
      return (
        <div
          className="rounded-lg border border-red-900/50 bg-red-950/30 p-6 flex items-start gap-4"
          role="alert"
        >
          <AlertTriangle className="w-6 h-6 shrink-0 text-red-400" aria-hidden />
          <div>
            <h2 className="font-semibold text-red-200 mb-1">Something went wrong</h2>
            <p className="text-sm text-slate-400 mb-3">{this.state.error.message}</p>
            <button
              onClick={() => this.setState({ hasError: false })}
              className="text-sm text-sky-400 hover:text-sky-300"
            >
              Try again
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
