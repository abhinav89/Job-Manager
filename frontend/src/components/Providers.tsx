"use client";

import { QueryClientProvider } from "@tanstack/react-query";
import { Provider } from "react-redux";
import { queryClient } from "@/lib/queryClient";
import { store } from "@/lib/store";
import { Toaster } from "sonner";
import { AuthProvider } from "@/lib/authContext";
import { AuthModal } from "@/components/AuthModal";

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          {children}
          <AuthModal />
          <Toaster richColors position="top-right" closeButton />
        </AuthProvider>
      </QueryClientProvider>
    </Provider>
  );
}

