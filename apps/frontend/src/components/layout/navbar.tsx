"use client";

import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";

import { useCurrentUser } from "@/hooks/use-users";
import { logout } from "@/services/auth.service";

import { Button } from "@/components/ui/button";


export default function Navbar() {

    const router = useRouter();

    const queryClient = useQueryClient();

    const {
        data: currentUser,
        isLoading,
    } = useCurrentUser();


    function handleLogout() {

        logout();

        queryClient.clear();

        router.push("/login");

    }


    function handleLogin() {

        router.push("/login");

    }

    return (

        <header className="
            h-16
            border-b
            flex
            items-center
            justify-between
            px-6
            bg-white
        ">

            <div>

                <h2 className="font-semibold">
                    Security Operations Center
                </h2>

            </div>


            <div className="
                flex
                items-center
                gap-4
            ">

                <span className="
                    text-sm
                    text-green-600
                ">
                    ● System Online
                </span>


                {isLoading ? (

                    <div className="
                        text-sm
                        text-muted-foreground
                    ">
                        Loading user...
                    </div>

                ) : currentUser ? (

                    <>

                        <div className="text-right">

                            <p className="text-sm font-medium">
                                {currentUser.full_name}
                            </p>

                            <p className="
                                text-xs
                                text-muted-foreground
                                uppercase
                            ">
                                {currentUser.role}
                            </p>

                        </div>


                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleLogout}
                        >
                            Logout
                        </Button>

                    </>

                ) : (

                    <>

                        <div className="text-right">

                            <p className="text-sm font-medium">
                                Guest
                            </p>

                            <p className="
                                text-xs
                                text-muted-foreground
                            ">
                                Dev Mode
                            </p>

                        </div>


                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleLogin}
                        >
                            Login
                        </Button>

                    </>

                )}

            </div>

        </header>

    );
}