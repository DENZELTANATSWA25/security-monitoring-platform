"use client";

import { useState, type ReactNode } from "react";
import { Menu, PanelLeftClose, PanelLeftOpen } from "lucide-react";

import Sidebar from "./sidebar";
import Header from "./navbar";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetTitle,
} from "@/components/ui/sheet";

type AppLayoutProps = {
  children: ReactNode;
};

export default function AppLayout({
  children,
}: AppLayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="flex h-dvh overflow-hidden bg-background text-foreground">
      {/* Desktop sidebar */}
      <div className="hidden shrink-0 lg:block">
        <Sidebar collapsed={sidebarCollapsed} />
      </div>

      {/* Mobile navigation */}
      <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
        <SheetContent
          side="left"
          className="w-[280px] max-w-[85vw] border-sidebar-border bg-sidebar p-0"
        >
          <SheetTitle className="sr-only">
            Application navigation
          </SheetTitle>

          <Sidebar onNavigate={() => setMobileMenuOpen(false)} />
        </SheetContent>
      </Sheet>

      {/* Application workspace */}
      <div className="flex min-w-0 flex-1 flex-col">
        <div
          className="
            flex h-[72px] shrink-0 items-center
            border-b border-border bg-card
          "
        >
          <div className="flex items-center gap-2 px-3">
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              aria-label="Open navigation menu"
              onClick={() => setMobileMenuOpen(true)}
            >
              <Menu className="size-5" />
            </Button>

            <Button
              variant="ghost"
              size="icon"
              className="hidden lg:inline-flex"
              aria-label={
                sidebarCollapsed
                  ? "Expand sidebar"
                  : "Collapse sidebar"
              }
              aria-expanded={!sidebarCollapsed}
              onClick={() => setSidebarCollapsed((value) => !value)}
            >
              {sidebarCollapsed ? (
                <PanelLeftOpen className="size-5" />
              ) : (
                <PanelLeftClose className="size-5" />
              )}
            </Button>
          </div>

          <div className="min-w-0 flex-1">
            <Header />
          </div>
        </div>

        <main
          id="main-content"
          className="
            min-h-0 flex-1 overflow-y-auto
            bg-background
          "
        >
          <div
            className="
              mx-auto w-full max-w-[1600px]
              px-4 py-6
              sm:px-6
              lg:px-8 lg:py-8
            "
          >
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}