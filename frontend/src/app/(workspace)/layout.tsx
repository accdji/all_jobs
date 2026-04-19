import { headers } from "next/headers";
import { WorkspaceShell } from "@/components/workspace-shell";

export default async function WorkspaceLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const headersList = await headers();
  const pathname = headersList.get("x-pathname") ?? "/";

  return <WorkspaceShell pathname={pathname}>{children}</WorkspaceShell>;
}
