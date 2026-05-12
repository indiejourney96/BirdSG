"use client";

import { useState } from "react";
import api from "@/services/api";

export default function UploadBox() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  async function handleUpload(
    e: React.ChangeEvent<HTMLInputElement>
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

    } catch (err: any) {
      console.error(err);

      setError(
        err?.response?.data?.detail ||
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