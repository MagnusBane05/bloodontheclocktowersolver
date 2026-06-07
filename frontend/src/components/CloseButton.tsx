export function CloseButton({onClose}: {onClose: () => void;}) {
  return (
    <button
      type="button"
      onClick={onClose}
      aria-label="Close claim modal"
      className="text-white text-2xl leading-none hover:text-red-300 focus:outline-none"
    >
      ×
    </button>
  );
}