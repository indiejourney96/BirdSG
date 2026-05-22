const API_BASE_URL = "http://127.0.0.1:8000";

export async function predictBird(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Prediction failed");
  }

  return response.json();
}

export async function getBirdInfo(label: string) {
  const response = await fetch(`${API_BASE_URL}/birds/${label}`);

  if (!response.ok) {
    throw new Error("Failed to fetch bird info");
  }

  return response.json();
}