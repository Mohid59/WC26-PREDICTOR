import { flagUrl, flagSrcset } from "../lib/countries";
import { cn } from "../lib/cn";

type Size = "sm" | "md" | "lg" | "xl";
const SIZES: Record<Size, string> = {
  sm: "h-3.5 w-5",
  md: "h-5 w-7",
  lg: "h-7 w-10",
  xl: "h-10 w-14",
};

/** Country flag image with built-in fallback for missing codes. */
export function Flag({
  code,
  name,
  size = "md",
  className,
  rounded = "rounded",
}: {
  code: string;
  name?: string;
  size?: Size;
  className?: string;
  rounded?: string;
}) {
  return (
    <img
      src={flagUrl(code, 80)}
      srcSet={flagSrcset(code)}
      alt={name ? `${name} flag` : `${code} flag`}
      width={40}
      height={30}
      loading="lazy"
      decoding="async"
      className={cn(
        "shrink-0 object-cover ring-1 ring-white/10 shadow-sm",
        SIZES[size],
        rounded,
        className
      )}
    />
  );
}
