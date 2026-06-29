"use client";

const APP_ENV = process.env.NEXT_PUBLIC_APP_ENV ?? "development";

export function EnvironmentBanner() {
  if (APP_ENV === "production") {
    return null;
  }

  const label =
    APP_ENV === "staging"
      ? "Staging environment — not production data"
      : `Development (${APP_ENV})`;

  return (
    <div
      className="fixed top-0 left-0 right-0 z-[100] bg-amber-500/90 text-black text-center text-[12px] font-semibold py-1.5 px-4 md:pl-64"
      role="status"
    >
      {label}
    </div>
  );
}
