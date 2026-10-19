"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { supabase } from "@/lib/supabase-client";
import { ShieldAlert, ArrowLeft, Loader2, Sparkles, Mail } from "lucide-react";

export default function SignupPage() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  
  // OTP Verification flow state
  const [showOtpInput, setShowOtpInput] = useState(false);
  const [otpCode, setOtpCode] = useState("");
  const [verifying, setVerifying] = useState(false);

  const router = useRouter();

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
          },
        },
      });

      if (error) throw error;

      // Check if user is already confirmed (if email confirmation is turned off in Supabase)
      if (data.user && data.user.identities && data.user.identities.length > 0) {
        // If auto-confirmed, redirect straight away
        if (data.session) {
          setSuccess(true);
          setTimeout(() => {
            router.push("/dashboard");
          }, 1500);
          return;
        }
      }

      setSuccess(true);
      setShowOtpInput(true);
    } catch (err: any) {
      console.error("Signup error:", err);
      setError(err.message || "Failed to create account");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setVerifying(true);
    setError(null);

    try {
      const { error } = await supabase.auth.verifyOtp({
        email,
        token: otpCode,
        type: "signup",
      });

      if (error) throw error;

      // OTP Verification Success! Redirect to dashboard
      router.push("/dashboard");
    } catch (err: any) {
      console.error("OTP verification error:", err);
      setError(err.message || "Invalid or expired verification code");
    } finally {
      setVerifying(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-950/30 via-zinc-950 to-black text-zinc-100 p-6 font-sans relative overflow-hidden">
      
      {/* Decorative Background */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1f293706_1px,transparent_1px),linear-gradient(to_bottom,#1f293706_1px,transparent_1px)] bg-[size:4rem_4rem] pointer-events-none" />
      <div className="absolute top-[20%] left-[50%] -translate-x-1/2 w-[350px] h-[350px] bg-indigo-500/5 rounded-full blur-[80px] pointer-events-none" />

      {/* Back Link */}
      <Link
        href="/"
        className="absolute top-6 left-6 inline-flex items-center gap-2 text-xs text-zinc-500 hover:text-zinc-300 transition-all"
      >
        <ArrowLeft size={14} /> Back to home
      </Link>

      <div className="w-full max-w-md bg-zinc-900/60 border border-zinc-800/80 rounded-2xl p-8 shadow-2xl backdrop-blur-md space-y-6 relative z-10">
        
        {/* Header */}
        <div className="space-y-2 text-center">
          <div className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-500/10 border border-indigo-500/25 text-indigo-400 mb-2">
            {showOtpInput ? <Mail size={16} /> : <Sparkles size={16} />}
          </div>
          <h1 className="text-3xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-zinc-100 to-indigo-200">
            {showOtpInput ? "Verify Your Email" : "Create Account"}
          </h1>
          <p className="text-xs text-zinc-400">
            {showOtpInput 
              ? `We sent a 6-digit confirmation code to ${email}`
              : "Start building your private Agentic AI Knowledge Assistant database."}
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs p-3.5 rounded-xl flex items-start gap-2.5">
            <ShieldAlert size={14} className="flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {/* Success Alert */}
        {success && !showOtpInput && (
          <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs p-3.5 rounded-xl text-center">
            Account created successfully! Redirecting to Dashboard...
          </div>
        )}

        {success && showOtpInput && (
          <div className="bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs p-3.5 rounded-xl text-center">
            Please enter the 6-digit verification code sent to your email.
          </div>
        )}

        {/* Form Selection */}
        {!showOtpInput ? (
          <form onSubmit={handleSignup} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider" htmlFor="fullName">
                Full Name
              </label>
              <input
                id="fullName"
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Alex Johnson"
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3.5 text-sm text-zinc-100 placeholder-zinc-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-transparent transition-all"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider" htmlFor="email">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="alex@example.com"
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3.5 text-sm text-zinc-100 placeholder-zinc-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-transparent transition-all"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3.5 text-sm text-zinc-100 placeholder-zinc-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-transparent transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={loading || success}
              className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-600/50 text-white font-semibold rounded-xl py-3.5 text-sm shadow-lg hover:shadow-indigo-500/10 transition-all flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Registering...
                </>
              ) : (
                "Sign Up"
              )}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerifyOtp} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-zinc-400 uppercase tracking-wider" htmlFor="otpCode">
                6-Digit Verification Code
              </label>
              <input
                id="otpCode"
                type="text"
                required
                maxLength={6}
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ""))}
                placeholder="123456"
                className="w-full bg-zinc-950 border border-zinc-800 rounded-xl px-4 py-3.5 text-center text-lg font-bold text-zinc-100 placeholder-zinc-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-transparent tracking-widest transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={verifying}
              className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-600/50 text-white font-semibold rounded-xl py-3.5 text-sm shadow-lg hover:shadow-indigo-500/10 transition-all flex items-center justify-center gap-2"
            >
              {verifying ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Verifying...
                </>
              ) : (
                "Verify Code"
              )}
            </button>

            <button
              type="button"
              onClick={() => setShowOtpInput(false)}
              className="w-full bg-zinc-950 hover:bg-zinc-900 border border-zinc-800 text-zinc-400 font-semibold rounded-xl py-3.5 text-sm shadow-lg transition-all"
            >
              Back to Sign Up
            </button>
          </form>
        )}

        {/* Footer info */}
        <div className="text-center text-xs text-zinc-500 border-t border-zinc-800/80 pt-5">
          Already have an account?{" "}
          <Link href="/login" className="text-indigo-400 hover:text-indigo-300 font-semibold hover:underline">
            Sign In
          </Link>
        </div>
      </div>
    </main>
  );
}
