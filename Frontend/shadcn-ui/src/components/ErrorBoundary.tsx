import React from 'react';

type Props = { children: React.ReactNode };
type State = { hasError: boolean; error?: any };

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError(error: any) { return { hasError: true, error }; }
  componentDidCatch(error: any, info: any) { 
    try { console.error('ErrorBoundary', error, info); } catch {}
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center text-center text-white bg-black p-6">
          <div>
            <h1 className="text-2xl font-bold mb-2">Se produjo un error en la interfaz</h1>
            <p className="text-neutral-300 text-sm mb-4">Prueba a volver atrás o ir al inicio.</p>
            <div className="space-x-3">
              <a className="underline" href="/">Inicio</a>
              <a className="underline" href="/debug">Debug</a>
            </div>
            {this.state.error && (
              <div className="mt-4 text-xs text-neutral-400 max-w-lg mx-auto break-words">
                {String(this.state.error)}
              </div>
            )}
          </div>
        </div>
      );
    }
    return this.props.children as any;
  }
}
