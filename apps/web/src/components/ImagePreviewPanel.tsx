
interface ImagePreviewPanelProps {
  url: string | null
  alt?: string
  onClose: () => void
}

export function ImagePreviewPanel({ url, alt, onClose }: ImagePreviewPanelProps) {
  if (!url) return null

  return (
    <>
      <div
        className="fixed inset-0 bg-black/80 z-40 flex items-center justify-center p-4"
        onClick={onClose}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Escape' && onClose()}
        aria-label="Close preview"
      >
        <div
          className="max-w-[90vw] max-h-[90vh] flex items-center justify-center"
          onClick={(e) => e.stopPropagation()}
        >
          <img
            src={url}
            alt={alt ?? 'Preview'}
            className="max-w-full max-h-[90vh] object-contain rounded"
          />
        </div>
      </div>
    </>
  )
}
