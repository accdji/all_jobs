import { AiConfigPanel } from "@/components/ai-config-panel";
import { getJson } from "@/lib/api";
import { AiConfigResponse } from "@/lib/types";

export default async function AiConfigPage() {
  const data = await getJson<AiConfigResponse>("ai-config");

  return <AiConfigPanel initialData={data} />;
}
