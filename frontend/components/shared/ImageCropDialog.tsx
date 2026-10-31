"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import Cropper from "react-easy-crop";
import type { Area, Point } from "react-easy-crop";
import "react-easy-crop/react-easy-crop.css";
import {
  cropImageToFile,
  isSupportedImageFile,
  MAX_ORIGINAL_FILE_BYTES,
} from "@/lib/cropImage";

interface ImageCropDialogProps {
  file: File;
  previewUrl: string;
  onCancel: () => void;
  onComplete: (file: File) => void;
}

export default function ImageCropDialog({
  file,
  previewUrl,
  onCancel,
  onComplete,
}: ImageCropDialogProps) {
  const titleId = useId();
  const descriptionId = useId();
  const dialogRef = useRef<HTMLDivElement>(null);
  const [crop, setCrop] = useState<Point>({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [croppedAreaPixels, setCroppedAreaPixels] = useState<Area | null>(null);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(() =>
    isSupportedImageFile(file)
      ? null
      : "Please choose a JPEG, PNG, or WebP image.",
  );

  const supported = isSupportedImageFile(file);
  const originalTooLarge = file.size > MAX_ORIGINAL_FILE_BYTES;
  const canUseOriginal = supported && !originalTooLarge;

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    const previouslyFocused =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    const dialog = dialogRef.current;

    document.body.style.overflow = "hidden";
    dialog?.focus();

    function handleTabKey(event: KeyboardEvent) {
      if (event.key !== "Tab" || !dialog) {
        return;
      }

      const focusableElements = Array.from(
        dialog.querySelectorAll<HTMLElement>(
          'button:not([disabled]), input:not([disabled]), [href], select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ),
      );

      if (focusableElements.length === 0) {
        return;
      }

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (event.shiftKey && document.activeElement === firstElement) {
        event.preventDefault();
        lastElement.focus();
      } else if (!event.shiftKey && document.activeElement === lastElement) {
        event.preventDefault();
        firstElement.focus();
      }
    }

    document.addEventListener("keydown", handleTabKey);

    return () => {
      document.removeEventListener("keydown", handleTabKey);
      document.body.style.overflow = previousOverflow;
      previouslyFocused?.focus();
    };
  }, []);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !processing) {
        onCancel();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [onCancel, processing]);

  const handleCropComplete = useCallback(
    (_croppedArea: Area, croppedAreaPixelsResult: Area) => {
      setCroppedAreaPixels(croppedAreaPixelsResult);
    },
    [],
  );

  async function handleApplyCrop() {
    if (!croppedAreaPixels || processing) {
      return;
    }

    try {
      setProcessing(true);
      setError(null);

      const croppedFile = await cropImageToFile(
        previewUrl,
        croppedAreaPixels,
        file.name,
      );

      onComplete(croppedFile);
    } catch (cropError) {
      console.error(cropError);
      setError(
        cropError instanceof Error
          ? cropError.message
          : "Could not crop this image. Please try another photo.",
      );
      setProcessing(false);
    }
  }

  function handleUseOriginal() {
    if (!canUseOriginal || processing) {
      return;
    }

    onComplete(file);
  }

  function handleCancel() {
    if (!processing) {
      onCancel();
    }
  }

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          handleCancel();
        }
      }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        tabIndex={-1}
        className="flex max-h-[calc(100dvh-2rem)] w-full max-w-[32rem] flex-col overflow-hidden rounded-2xl bg-surface shadow-2xl outline-none"
      >
        <div className="flex items-start justify-between gap-md p-md sm:p-lg">
          <div>
            <h2
              id={titleId}
              className="font-headline text-headline-md text-on-surface"
            >
              Crop photo
            </h2>
            <p
              id={descriptionId}
              className="mt-xs font-body text-body-md text-on-surface-variant"
            >
              Center the bird in the square frame for a clearer identification.
            </p>
          </div>

          <button
            type="button"
            onClick={handleCancel}
            disabled={processing}
            aria-label="Close crop dialog"
            className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-on-surface-variant transition-colors hover:bg-surface-variant disabled:cursor-not-allowed disabled:opacity-50"
          >
            <span className="material-symbols-outlined">close</span>
          </button>
        </div>

        <div className="relative h-[min(55vh,400px)] w-full overflow-hidden bg-black">
          {supported ? (
            <Cropper
              image={previewUrl}
              crop={crop}
              zoom={zoom}
              aspect={1}
              cropShape="rect"
              showGrid
              disableAutomaticStylesInjection
              onCropChange={setCrop}
              onZoomChange={setZoom}
              onCropComplete={handleCropComplete}
              mediaProps={{
                onError: () =>
                  setError(
                    "The selected file could not be loaded as an image.",
                  ),
              }}
              classes={{
                cropAreaClassName: "rounded-lg",
              }}
              style={{
                cropAreaStyle: {
                  borderColor: "rgba(255, 255, 255, 0.9)",
                },
              }}
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center px-lg text-center">
              <p className="font-body text-body-md text-white/90">{error}</p>
            </div>
          )}
        </div>

        <div className="flex flex-col gap-md p-md sm:p-lg">
          {supported && (
            <label className="flex items-center gap-sm">
              <span className="material-symbols-outlined text-[20px] text-on-surface-variant">
                zoom_out
              </span>
              <input
                type="range"
                min={1}
                max={4}
                step={0.01}
                value={zoom}
                onChange={(event) => setZoom(Number(event.target.value))}
                aria-label="Zoom"
                className="h-2 w-full cursor-pointer accent-primary"
              />
              <span className="material-symbols-outlined text-[20px] text-on-surface-variant">
                zoom_in
              </span>
            </label>
          )}

          {!error && originalTooLarge && (
            <p className="font-body text-sm text-on-surface-variant">
              The original photo is larger than 10 MB. Apply a crop to continue.
            </p>
          )}

          {error && (
            <div
              role="alert"
              className="flex items-start gap-sm rounded-lg border border-error/30 bg-error-container px-md py-sm text-on-error-container"
            >
              <span className="material-symbols-outlined text-[20px]">
                error
              </span>
              <p className="font-body text-sm">{error}</p>
            </div>
          )}

          <div className="flex flex-col-reverse gap-sm sm:flex-row sm:items-center sm:justify-between">
            <button
              type="button"
              onClick={handleCancel}
              disabled={processing}
              className="rounded-full px-md py-sm font-label-md text-label-md text-on-surface-variant transition-colors hover:bg-surface-variant disabled:cursor-not-allowed disabled:opacity-50"
            >
              Cancel
            </button>

            <div className="flex flex-col gap-sm sm:flex-row">
              <button
                type="button"
                onClick={handleUseOriginal}
                disabled={!canUseOriginal || processing}
                title={
                  originalTooLarge
                    ? "The original photo is larger than 10 MB."
                    : undefined
                }
                className="rounded-full border border-surface-variant px-md py-sm font-label-md text-label-md text-on-surface transition-colors hover:bg-surface-variant disabled:cursor-not-allowed disabled:opacity-50"
              >
                Use original
              </button>

              <button
                type="button"
                onClick={handleApplyCrop}
                disabled={!croppedAreaPixels || processing}
                className="inline-flex items-center justify-center gap-2 rounded-full bg-primary px-lg py-sm font-label-md text-label-md text-on-primary shadow-md transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {processing ? (
                  <>
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-on-primary/30 border-t-on-primary" />
                    Cropping...
                  </>
                ) : (
                  "Apply crop"
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
