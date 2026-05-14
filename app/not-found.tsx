import Link from "next/link";

export default function NotFound() {
  return (
    <div className="card text-center">
      <h1 className="text-xl font-semibold">Not found</h1>
      <p className="mt-2 text-sm text-muted">
        That page or match doesn&apos;t exist.{" "}
        <Link href="/" className="text-brand hover:underline">Back to dashboard</Link>.
      </p>
    </div>
  );
}
