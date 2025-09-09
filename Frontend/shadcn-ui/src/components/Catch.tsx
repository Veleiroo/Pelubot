import React from 'react';

export function Catch(props: { fallback: React.ReactNode; children: React.ReactNode }) {
  return <CatchBoundary fallback={props.fallback}>{props.children}</CatchBoundary>;
}

class CatchBoundary extends React.Component<{ fallback: React.ReactNode; children: React.ReactNode }, { hasError: boolean }> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }
  static getDerivedStateFromError(_error: any) { return { hasError: true }; }
  componentDidCatch(error: any, info: any) { try { console.error('CatchBoundary', error, info); } catch {} }
  render() {
    if (this.state.hasError) return this.props.fallback as any;
    return this.props.children as any;
  }
}

