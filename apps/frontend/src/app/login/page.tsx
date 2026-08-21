"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { login } from "@/services/auth.service";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";


export default function LoginPage() {
    const router = useRouter();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const [isSubmitting, setIsSubmitting] =
        useState(false);

    const [error, setError] =
        useState<string | null>(null);


    async function handleSubmit(
        event: FormEvent<HTMLFormElement>
    ) {
        event.preventDefault();

        setError(null);

        try {
            setIsSubmitting(true);

            await login({
                email,
                password,
            });

            router.push("/");

        } catch {
            setError(
                "Invalid email or password."
            );

        } finally {
            setIsSubmitting(false);
        }
    }


    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-100">

            <Card className="w-full max-w-md">

                <CardHeader>

                    <CardTitle>
                        Security SOC Login
                    </CardTitle>

                </CardHeader>

                <CardContent>

                    <form
                        onSubmit={handleSubmit}
                        className="space-y-4"
                    >

                        <Input
                            type="email"
                            placeholder="Email"
                            value={email}
                            onChange={(event) =>
                                setEmail(event.target.value)
                            }
                            required
                        />

                        <Input
                            type="password"
                            placeholder="Password"
                            value={password}
                            onChange={(event) =>
                                setPassword(event.target.value)
                            }
                            required
                        />

                        {error && (
                            <p className="text-sm text-red-600">
                                {error}
                            </p>
                        )}

                        <Button
                            type="submit"
                            className="w-full"
                            disabled={isSubmitting}
                        >
                            {isSubmitting
                                ? "Signing in..."
                                : "Sign in"}
                        </Button>

                    </form>

                </CardContent>

            </Card>

        </div>
    );
}