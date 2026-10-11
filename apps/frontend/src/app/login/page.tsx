"use client";

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  ArrowRight,
  LockKeyhole,
  Radar,
  ShieldCheck,
} from "lucide-react";

import { login } from "@/services/auth.service";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import ThemeSelector from "@/components/theme/theme-selector";

export default function LoginPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    try {
      setIsSubmitting(true);

      await login({
        email,
        password,
      });

      queryClient.clear();
      router.replace("/");
    } catch {
      setError("Invalid email or password.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-dvh bg-background text-foreground">
      {/* Branding panel — desktop */}
      <section
        className="
          relative hidden w-1/2 flex-col justify-between
          overflow-hidden border-r border-border
          bg-card p-10 lg:flex xl:p-14
        "
      >
        <div
          aria-hidden="true"
          className="
            pointer-events-none absolute -right-32 top-1/4
            size-[420px] rounded-full bg-primary/10 blur-3xl
          "
        />

        <div className="relative z-10 flex items-center gap-3">
          <div
            className="
              flex size-12 items-center justify-center
              rounded-xl border border-primary/25
              bg-primary/10 text-primary
            "
          >
            <ShieldCheck className="size-6" aria-hidden="true" />
          </div>

          <div>
            <p className="font-semibold tracking-tight">
              Security SOC
            </p>

            <p className="text-xs text-muted-foreground">
              Threat Monitoring Platform
            </p>
          </div>
        </div>

        <div className="relative z-10 max-w-xl">
          <div
            className="
              mb-6 inline-flex items-center gap-2
              rounded-full border border-border
              bg-background/70 px-3 py-1.5
              text-xs font-medium text-muted-foreground
            "
          >
            <span className="size-2 rounded-full bg-status-success" />
            Security Operations Center
          </div>

          <h1
            className="
              text-4xl font-bold tracking-tight
              xl:text-5xl
            "
          >
            Visibility.
            <br />
            Detection.
            <br />
            <span className="text-primary">
              Response.
            </span>
          </h1>

          <p className="mt-6 max-w-md leading-7 text-muted-foreground">
            Monitor security events, investigate suspicious
            activity, and respond to threats from one
            integrated security workspace.
          </p>

          <div className="mt-10 grid gap-3 sm:grid-cols-3">
            {[
              {
                icon: Activity,
                label: "Event monitoring",
              },
              {
                icon: Radar,
                label: "Threat detection",
              },
              {
                icon: LockKeyhole,
                label: "Secure access",
              },
            ].map(({ icon: Icon, label }) => (
              <div
                key={label}
                className="
                  flex flex-col gap-3 rounded-xl
                  border border-border bg-background/70 p-4
                "
              >
                <Icon
                  className="size-5 text-primary"
                  aria-hidden="true"
                />

                <span className="text-xs font-medium">
                  {label}
                </span>
              </div>
            ))}
          </div>
        </div>

        <p className="relative z-10 text-xs text-muted-foreground">
          Security SOC · Authorized access only
        </p>
      </section>

      {/* Authentication panel */}
      <section
        className="
          flex min-w-0 flex-1 flex-col
          px-5 py-6 sm:px-10 lg:px-12
        "
      >
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 lg:hidden">
            <div
              className="
                flex size-10 items-center justify-center
                rounded-lg border border-primary/25
                bg-primary/10 text-primary
              "
            >
              <ShieldCheck
                className="size-5"
                aria-hidden="true"
              />
            </div>

            <div>
              <p className="text-sm font-semibold">
                Security SOC
              </p>

              <p className="text-[11px] text-muted-foreground">
                Threat Monitoring Platform
              </p>
            </div>
          </div>

          <div className="ml-auto">
            <ThemeSelector />
          </div>
        </div>

        <div
          className="
            flex flex-1 items-center justify-center
            py-12
          "
        >
          <div className="w-full max-w-md">
            <div className="mb-8">
              <div
                className="
                  mb-4 flex size-12 items-center justify-center
                  rounded-xl border border-primary/25
                  bg-primary/10 text-primary
                "
              >
                <LockKeyhole
                  className="size-6"
                  aria-hidden="true"
                />
              </div>

              <h2 className="text-3xl font-bold tracking-tight">
                Welcome back
              </h2>

              <p className="mt-2 text-sm text-muted-foreground">
                Sign in to access your security operations workspace.
              </p>
            </div>

            <Card className="border-border bg-card shadow-sm">
              <CardHeader>
                <CardTitle className="text-base">
                  Sign in to your account
                </CardTitle>
              </CardHeader>

              <CardContent>
                <form
                  onSubmit={handleSubmit}
                  className="space-y-5"
                >
                  <div className="space-y-2">
                    <label
                      htmlFor="login-email"
                      className="text-sm font-medium"
                    >
                      Email address
                    </label>

                    <Input
                      id="login-email"
                      type="email"
                      placeholder="name@organization.com"
                      autoComplete="username"
                      value={email}
                      onChange={(event) =>
                        setEmail(event.target.value)
                      }
                      disabled={isSubmitting}
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <label
                      htmlFor="login-password"
                      className="text-sm font-medium"
                    >
                      Password
                    </label>

                    <Input
                      id="login-password"
                      type="password"
                      placeholder="Enter your password"
                      autoComplete="current-password"
                      value={password}
                      onChange={(event) =>
                        setPassword(event.target.value)
                      }
                      disabled={isSubmitting}
                      required
                    />
                  </div>

                  {error && (
                    <p
                      role="alert"
                      className="
                        rounded-lg border border-destructive/30
                        bg-destructive/10 p-3
                        text-sm text-destructive
                      "
                    >
                      {error}
                    </p>
                  )}

                  <Button
                    type="submit"
                    className="w-full"
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? (
                      "Signing in..."
                    ) : (
                      <>
                        Sign in
                        <ArrowRight
                          className="ml-2 size-4"
                          aria-hidden="true"
                        />
                      </>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>

            <p
              className="
                mt-6 text-center text-xs
                text-muted-foreground
              "
            >
              Protected workspace · Authorized personnel only
            </p>
          </div>
        </div>

        <p
          className="
            text-center text-xs text-muted-foreground
            lg:text-right
          "
        >
          Security SOC · Threat Monitoring Platform
        </p>
      </section>
    </main>
  );
}