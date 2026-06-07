export function Toggle ({checked, onChange, id}: {checked: boolean; onChange: (b: boolean) => void; id: string}) {
  return (
    <span
      className={`relative inline-flex h-6 w-11 flex-shrink-0 items-center rounded-full transition-colors duration-200 ease-in-out ring-gray-600 ${
        checked ? 'bg-indigo-600' : 'bg-gray-700'
      } ring-1 ring-inset ring-gray-700 hover:ring-gray-500`}
    >
      <input
        id={id}
        type="checkbox"
        checked={checked ?? false}
        onChange={(e) => onChange(e.target.checked)}
        className="absolute inset-0 h-full w-full opacity-0 cursor-pointer z-10"
      />
      <span
        aria-hidden="true"
        className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition duration-200 ease-in-out pointer-events-none ${
          checked ? 'translate-x-5' : 'translate-x-1'
        }`}
      />
    </span>
  );
}