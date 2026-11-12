"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role?: string;
}

interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isAuthModalOpen: boolean;
  setIsAuthModalOpen: (open: boolean) => void;
  login: (email: string, passcode?: string) => Promise<{ success: boolean; error?: string }>;
  loginWithGoogle: () => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = "job_manager_auth_session";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  // Initialize session from localStorage on client-side
  useEffect(() => {
    try {
      if (typeof window !== "undefined") {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
          const parsed = JSON.parse(stored) as AuthUser;
          if (parsed && parsed.email) {
            setUser(parsed);
          }
        }
      }
    } catch (err) {
      console.warn("Failed to read auth session:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = async (email: string, passcode?: string) => {
    const cleanEmail = (email || "").trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes("@")) {
      return { success: false, error: "Please enter a valid email address." };
    }

    // Determine user profile based on email
    let displayName = cleanEmail.split("@")[0];
    displayName = displayName.charAt(0).toUpperCase() + displayName.slice(1);

    if (cleanEmail === "abhinava2015@email.iimcal.ac.in" || cleanEmail.startsWith("abhinav")) {
      displayName = "Abhinav Agrawal";
    }

    const authUser: AuthUser = {
      id: btoa(cleanEmail).substring(0, 16),
      name: displayName,
      email: cleanEmail,
      role: "owner",
    };

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(authUser));
      setUser(authUser);
      setIsAuthModalOpen(false);
      toast.success(`Welcome back, ${displayName}!`);
      // Refetch user profile and workspace
      void queryClient.invalidateQueries({ queryKey: ["workspace-data"] });
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message || "Failed to save login session." };
    }
  };

  const loginWithGoogle = async () => {
    // Standard mock/direct Google OAuth sign-in flow
    // In production, this can redirect to Supabase Google OAuth endpoint
    const defaultGoogleUser: AuthUser = {
      id: "google-user-1",
      name: "Abhinav Agrawal",
      email: "abhinava2015@email.iimcal.ac.in",
      role: "owner",
    };

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(defaultGoogleUser));
      setUser(defaultGoogleUser);
      setIsAuthModalOpen(false);
      toast.success("Signed in with Google successfully!");
      void queryClient.invalidateQueries({ queryKey: ["workspace-data"] });
    } catch (err) {
      toast.error("Google sign-in failed. Please try email login.");
    }
  };

  const logout = () => {
    try {
      if (typeof window !== "undefined") {
        localStorage.removeItem(STORAGE_KEY);
      }
      setUser(null);
      // Purge all query caches so no private user data lingers
      queryClient.clear();
      toast.success("You have been signed out successfully.");
    } catch (err) {
      console.warn("Logout error:", err);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        isAuthModalOpen,
        setIsAuthModalOpen,
        login,
        loginWithGoogle,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
