import { redirect } from "next/navigation";

/**
 * Root page — redirects to Dashboard.
 */
export default function Home() {
  redirect("/dashboard");
}
