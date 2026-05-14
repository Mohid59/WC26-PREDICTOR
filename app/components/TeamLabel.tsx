import { Flag } from "./Flag";
import { cn } from "../lib/cn";

type Size = "sm" | "md" | "lg";

export function TeamLabel({
  code,
  name,
  size = "md",
  align = "left",
  showCode = false,
  className,
}: {
  code: string;
  name: string;
  size?: Size;
  align?: "left" | "right";
  showCode?: boolean;
  className?: string;
}) {
  const text = size === "lg" ? "text-lg" : size === "sm" ? "text-sm" : "text-base";
  const flagSize: "sm" | "md" | "lg" = size === "lg" ? "lg" : size === "sm" ? "sm" : "md";
  return (
    <div
      className={cn(
        "flex min-w-0 items-center gap-2.5",
        align === "right" && "flex-row-reverse",
        className
      )}
    >
      <Flag code={code} name={name} size={flagSize} />
      <span className={cn("min-w-0 truncate font-semibold tracking-tight", text)}>{name}</span>
      {showCode ? (
        <span className="hidden font-mono text-[10px] uppercase tracking-wider text-muted md:inline">
          {code}
        </span>
      ) : null}
    </div>
  );
}
