"use client";

import { useEffect } from "react";
import Alert from "@/components/Alert";
import Button, { ButtonLink } from "@/components/Button";

export default function AuthenticatedError({ error, unstable_retry }: { error: Error & { digest?: string }; unstable_retry: () => void }) {
  useEffect(() => {
    console.error("Authenticated route error", error);
  }, [error]);

  return (
    <div className="flex min-h-full items-center justify-center bg-slate-50 p-6 font-sans">
      <Alert className="w-full max-w-md bg-white border border-slate-200 shadow-sm rounded-2xl p-6">
        <h2 className="font-bold text-slate-900 text-lg">Unable to load this section</h2>
        <p className="mt-2 text-xs text-slate-500 leading-relaxed">
          An unexpected error occurred while loading this view. You can retry or return to your DealOS Jobs Dashboard.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Button variant="primary" size="md" onClick={unstable_retry}>Try again</Button>
          <ButtonLink variant="outline" size="md" href="/dashboard">Return to Dashboard</ButtonLink>
        </div>
      </Alert>
    </div>
  );
}
