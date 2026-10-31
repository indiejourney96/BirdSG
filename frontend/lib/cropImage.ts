import type { Area } from "react-easy-crop";

const MAX_OUTPUT_SIZE = 1600;
const JPEG_QUALITY = 0.9;

const SUPPORTED_IMAGE_TYPES = new Set([
  "image/jpeg",
  "image/png",
  "image/webp",
]);

const SUPPORTED_IMAGE_EXTENSIONS = /\.(jpe?g|png|webp)$/i;

export const MAX_ORIGINAL_FILE_BYTES = 10 * 1024 * 1024;

interface LoadedImage {
  source: CanvasImageSource;
  width: number;
  height: number;
  release?: () => void;
}

export function isSupportedImageFile(file: File): boolean {
  return (
    SUPPORTED_IMAGE_TYPES.has(file.type) ||
    (!file.type && SUPPORTED_IMAGE_EXTENSIONS.test(file.name))
  );
}

async function loadImage(imageSrc: string): Promise<LoadedImage> {
  const response = await fetch(imageSrc);

  if (!response.ok) {
    throw new Error("Could not read the selected image.");
  }

  const blob = await response.blob();

  if (typeof createImageBitmap === "function") {
    try {
      const bitmap = await createImageBitmap(blob, {
        imageOrientation: "from-image",
      });

      return {
        source: bitmap,
        width: bitmap.width,
        height: bitmap.height,
        release: () => bitmap.close(),
      };
    } catch {
      // Fall back to an HTMLImageElement when the browser cannot decode the blob.
    }
  }

  const objectUrl = URL.createObjectURL(blob);

  try {
    const image = await new Promise<HTMLImageElement>((resolve, reject) => {
      const element = new Image();
      element.onload = () => resolve(element);
      element.onerror = () =>
        reject(
          new Error(
            "The selected file could not be loaded as an image.",
          ),
        );
      element.src = objectUrl;
    });

    return {
      source: image,
      width: image.naturalWidth,
      height: image.naturalHeight,
    };
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}

function canvasToBlob(canvas: HTMLCanvasElement): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => {
        if (blob) {
          resolve(blob);
          return;
        }

        reject(new Error("Could not create the cropped image."));
      },
      "image/jpeg",
      JPEG_QUALITY,
    );
  });
}

function getCroppedFileName(originalFileName: string): string {
  const baseName = originalFileName.replace(/\.[^.]+$/, "").trim();
  return `${baseName || "bird"}-cropped.jpg`;
}

export async function cropImageToFile(
  imageSrc: string,
  cropPixels: Area,
  originalFileName: string,
): Promise<File> {
  if (cropPixels.width <= 0 || cropPixels.height <= 0) {
    throw new Error("Please select a valid crop area.");
  }

  const image = await loadImage(imageSrc);

  try {
    const sourceX = Math.max(0, Math.min(cropPixels.x, image.width));
    const sourceY = Math.max(0, Math.min(cropPixels.y, image.height));
    const sourceWidth = Math.min(
      cropPixels.width,
      image.width - sourceX,
    );
    const sourceHeight = Math.min(
      cropPixels.height,
      image.height - sourceY,
    );

    if (sourceWidth <= 0 || sourceHeight <= 0) {
      throw new Error("Please select a valid crop area.");
    }

    const outputSize = Math.min(
      MAX_OUTPUT_SIZE,
      Math.max(1, Math.round(Math.max(sourceWidth, sourceHeight))),
    );

    const canvas = document.createElement("canvas");
    canvas.width = outputSize;
    canvas.height = outputSize;

    const context = canvas.getContext("2d");

    if (!context) {
      throw new Error("Your browser could not process this image.");
    }

    context.imageSmoothingEnabled = true;
    context.imageSmoothingQuality = "high";
    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, outputSize, outputSize);
    context.drawImage(
      image.source,
      sourceX,
      sourceY,
      sourceWidth,
      sourceHeight,
      0,
      0,
      outputSize,
      outputSize,
    );

    const blob = await canvasToBlob(canvas);

    return new File([blob], getCroppedFileName(originalFileName), {
      type: "image/jpeg",
      lastModified: Date.now(),
    });
  } finally {
    image.release?.();
  }
}
