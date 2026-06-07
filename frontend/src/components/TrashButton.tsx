export function TrashButton({onClick}: {onClick: React.MouseEventHandler<HTMLButtonElement>}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className='hover:text-red-300 hover:border-red-300'
    >
      <span className='pi pi-trash' />
    </button>
  );
}