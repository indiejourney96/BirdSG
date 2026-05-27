const API_BASE_URL = "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function getErrorDetail(response: Response): Promise<unknown> {
  try {
    const body = await response.json();
    return body.detail ?? body;
  } catch {
    return await response.text();
  }
}

function formatApiErrorMessage(status: number, detail: unknown, fallback: string): string {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (
    detail &&
    typeof detail === "object" &&
    "error" in detail &&
    typeof detail.error === "string" &&
    detail.error.trim()
  ) {
    return detail.error;
  }

  return `${fallback} (${status})`;
}

export async function predictBird(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const detail = await getErrorDetail(response);
    throw new ApiError(
      response.status,
      detail,
      formatApiErrorMessage(response.status, detail, "Prediction failed"),
    );
  }

  return response.json();
}

export async function getBirdInfo(label: string) {
  const response = await fetch(`${API_BASE_URL}/birds/${label}`);

  if (!response.ok) {
    const detail = await getErrorDetail(response);
    throw new ApiError(
      response.status,
      detail,
      formatApiErrorMessage(response.status, detail, "Failed to fetch bird info"),
    );
  }

  return response.json();
}

export async function getSighting(sightingId: string) {
  const response = await fetch(`${API_BASE_URL}/sightings/${sightingId}`);

  if (!response.ok) {
    const detail = await getErrorDetail(response);
    throw new ApiError(
      response.status,
      detail,
      formatApiErrorMessage(response.status, detail, "Failed to fetch sighting"),
    );
  }

  return response.json();
}
