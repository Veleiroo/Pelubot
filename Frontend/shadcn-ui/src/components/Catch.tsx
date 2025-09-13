import React from 'react';

export function Catch(props: { fallback: React.ReactNode; children: React.ReactNode }) {
  return <CatchBoundary fallback={props.fallback}>{props.children}</CatchBoundary>;
}

class CatchBoundary extends React.Component<{ fallback: React.ReactNode; children: React.ReactNode }, { hasError: boolean }> {
  constructor(props: { fallback: React.ReactNode; children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError(_error: unknown) {
    return { hasError: true };
  }
  componentDidCatch(error: unknown, info: React.ErrorInfo) {
    console.error('CatchBoundary', error, info);
  }
  render() {
    if (this.state.hasError) return this.props.fallback;
    return this.props.children;
  }
}

