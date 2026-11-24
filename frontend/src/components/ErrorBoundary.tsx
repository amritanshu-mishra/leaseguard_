import { Component, type ErrorInfo, type ReactNode } from 'react';

interface State { error: Error | null }

/** Last line of defence: never leave the user with a blank white screen. */
export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('LeaseGuard UI error', error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    const hi = localStorage.getItem('leaseguard-lang') === 'hi';
    return (
      <div className="boundary" role="alert">
        <div className="boundary-card">
          <h1>{hi ? 'कुछ गलत हो गया' : 'Something went wrong'}</h1>
          <p>
            {hi
              ? 'स्क्रीन लोड नहीं हो सकी। आपका डेटा सुरक्षित है। कृपया दोबारा कोशिश करें।'
              : 'This screen could not be loaded. Your data is safe. Please try again.'}
          </p>
          <pre>{this.state.error.message}</pre>
          <button className="button button-primary" onClick={() => { this.setState({ error: null }); window.location.reload(); }}>
            {hi ? 'फिर से कोशिश करें' : 'Reload app'}
          </button>
        </div>
      </div>
    );
  }
}
