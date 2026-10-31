"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface PendingImage {
  file: File;
  previewUrl: string;
}

export function usePendingImage() {
  const [pendingImage, setPendingImage] = useState<PendingImage | null>(null);
  const previewUrlRef = useRef<string | null>(null);

  const clearPendingImage = useCallback(() => {
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current);
      previewUrlRef.current = null;
    }

    setPendingImage(null);
  }, []);

  const selectImage = useCallback((file: File) => {
    if (previewUrlRef.current) {
      URL.revokeObjectURL(previewUrlRef.current);
    }

    const previewUrl = URL.createObjectURL(file);
    previewUrlRef.current = previewUrl;
    setPendingImage({ file, previewUrl });
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrlRef.current) {
        URL.revokeObjectURL(previewUrlRef.current);
      }
    };
  }, []);

  return { pendingImage, selectImage, clearPendingImage };
}
