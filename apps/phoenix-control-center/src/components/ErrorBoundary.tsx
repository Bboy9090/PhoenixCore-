import React, { ReactNode, ReactElement } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactElement;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

/**
 * Error boundary component for catching React errors
 */
export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="p-8">
            <div className="card bg-red-50 dark:bg-red-900 border-red-200 dark:border-red-700">
              <div className="flex items-start gap-4">
                <AlertCircle className="text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" size={24} />
                <div className="flex-1">
                  <h3 className="font-semibold text-red-900 dark:text-red-100 mb-2">
                    Something went wrong
                  </h3>
                  <p className="text-red-800 dark:text-red-200 text-sm mb-4">
                    {this.state.error?.message || 'An unexpected error occurred'}
                  </p>
                  <button
                    onClick={this.handleReset}
                    className="btn-secondary flex items-center gap-2"
                  >
                    <RefreshCw size={16} />
                    Try Again
                  </button>
                </div>
              </div>
            </div>
          </div>
        )
      );
    }

    return this.props.children;
  }
}

/**
 * Error display component for non-fatal errors
 */
interface ErrorDisplayProps {
  error: string | null;
  onDismiss?: () => void;
}

export function ErrorDisplay({ error, onDismiss }: ErrorDisplayProps) {
  if (!error) return null;

  return (
    <div className="card bg-red-50 dark:bg-red-900 border-red-200 dark:border-red-700 animate-slideIn">
      <div className="flex items-start gap-3">
        <AlertCircle className="text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" size={20} />
        <div className="flex-1">
          <p className="text-red-800 dark:text-red-200 text-sm">{error}</p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Warning display component
 */
interface WarningDisplayProps {
  message: string;
  onDismiss?: () => void;
}

export function WarningDisplay({ message, onDismiss }: WarningDisplayProps) {
  return (
    <div className="card bg-yellow-50 dark:bg-yellow-900 border-yellow-200 dark:border-yellow-700 animate-slideIn">
      <div className="flex items-start gap-3">
        <div className="text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5">⚠️</div>
        <div className="flex-1">
          <p className="text-yellow-800 dark:text-yellow-200 text-sm">{message}</p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-yellow-600 dark:text-yellow-400 hover:text-yellow-700 dark:hover:text-yellow-300"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Success display component
 */
interface SuccessDisplayProps {
  message: string;
  onDismiss?: () => void;
}

export function SuccessDisplay({ message, onDismiss }: SuccessDisplayProps) {
  return (
    <div className="card bg-green-50 dark:bg-green-900 border-green-200 dark:border-green-700 animate-slideIn">
      <div className="flex items-start gap-3">
        <div className="text-green-600 dark:text-green-400 flex-shrink-0 mt-0.5">✓</div>
        <div className="flex-1">
          <p className="text-green-800 dark:text-green-200 text-sm">{message}</p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
}
