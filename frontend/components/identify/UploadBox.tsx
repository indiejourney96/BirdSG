"use client";

import { useState } from "react";
import type { ChangeEvent } from "react";
import api from "@/services/api";

interface UploadResponse {
  [key: string]: unknown;
}

export default function UploadBox() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState("");

  async function handleUpload(
    e: ChangeEvent<HTMLInputElement>
  ) {
    const file = e.target.files?.[0];

    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      setError("");

      const response = await api.post(
        "/predict",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setResult(response.data);

    } catch (err: unknown) {
      console.error(err);

      const detail =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;

      setError(
        detail ||
        "Prediction failed"
      );

    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">

      <input
        type="file"
        accept="image/*"
        onChange={handleUpload}
        className="block w-full"
      />

      {loading && (
        <div className="text-green-700 font-medium">
          Identifying bird...
        </div>
      )}

      {error && (
        <div className="text-red-600">
          {JSON.stringify(error)}
        </div>
      )}

      {result && (
        <div className="bg-white rounded-xl p-4 shadow">

          <h2 className="text-xl font-bold mb-4">
            Prediction Result
          </h2>

          <pre className="text-sm overflow-auto">
            {JSON.stringify(result, null, 2)}
          </pre>

        </div>
      )}

    </div>
  );
}
