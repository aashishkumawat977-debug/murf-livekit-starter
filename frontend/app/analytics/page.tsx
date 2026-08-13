'use client';

import { useEffect, useState } from 'react';

type Analytics = {
  total: number;
  successful: number;
  failed: number;
  successRate: number;
};

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function loadAnalytics() {
    try {
      setError(null);

      const response = await fetch('/api/analytics', {
        cache: 'no-store',
      });

      if (!response.ok) {
        throw new Error('Failed to load analytics');
      }

      const data = await response.json();
      setAnalytics(data);
    } catch {
      setError('Unable to load call analytics.');
    }
  }

  useEffect(() => {
    loadAnalytics();

    const interval = setInterval(loadAnalytics, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <main className="min-h-screen px-6 py-16 md:px-12">
      <div className="mx-auto max-w-6xl">
        <div className="mb-10">
          <p className="mb-2 text-sm font-medium uppercase tracking-wider text-muted-foreground">
            Day 8
          </p>

          <h1 className="text-4xl font-bold tracking-tight">
            Call Analytics
          </h1>

          <p className="mt-3 text-muted-foreground">
            Anisha Learning & Literacy performance overview
          </p>
        </div>

        {error && (
          <div className="mb-6 rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-destructive">
            {error}
          </div>
        )}

        {!analytics ? (
          <div className="rounded-2xl border p-8 text-muted-foreground">
            Loading analytics...
          </div>
        ) : (
          <>
            <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-2xl border p-6">
                <p className="text-sm text-muted-foreground">
                  Total Calls
                </p>
                <p className="mt-3 text-4xl font-bold">
                  {analytics.total}
                </p>
              </div>

              <div className="rounded-2xl border p-6">
                <p className="text-sm text-muted-foreground">
                  Successful Calls
                </p>
                <p className="mt-3 text-4xl font-bold">
                  {analytics.successful}
                </p>
              </div>

              <div className="rounded-2xl border p-6">
                <p className="text-sm text-muted-foreground">
                  Failed Calls
                </p>
                <p className="mt-3 text-4xl font-bold">
                  {analytics.failed}
                </p>
              </div>

              <div className="rounded-2xl border p-6">
                <p className="text-sm text-muted-foreground">
                  Success Rate
                </p>
                <p className="mt-3 text-4xl font-bold">
                  {analytics.successRate}%
                </p>
              </div>
            </div>

            <div className="mt-8 rounded-2xl border p-6">
              <h2 className="text-xl font-semibold">
                Current Call Performance
              </h2>

              <div className="mt-6 space-y-5">
                <div>
                  <div className="mb-2 flex justify-between text-sm">
                    <span>Successful</span>
                    <span>{analytics.successful}</span>
                  </div>

                  <div className="h-3 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-foreground"
                      style={{
                        width:
                          analytics.total > 0
                            ? `${(analytics.successful / analytics.total) * 100}%`
                            : '0%',
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="mb-2 flex justify-between text-sm">
                    <span>Failed</span>
                    <span>{analytics.failed}</span>
                  </div>

                  <div className="h-3 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-muted-foreground"
                      style={{
                        width:
                          analytics.total > 0
                            ? `${(analytics.failed / analytics.total) * 100}%`
                            : '0%',
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-8">
              <a
                href="/"
                className="text-sm font-medium underline underline-offset-4"
              >
                ← Back to Anisha
              </a>
            </div>
          </>
        )}
      </div>
    </main>
  );
}
