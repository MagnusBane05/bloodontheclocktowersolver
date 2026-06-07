interface ButtonProps {
  style: 'primary' | 'secondary' | 'remove';
  children: React.ReactNode;
  onClick?: React.MouseEventHandler<HTMLButtonElement>;
  disabled?: boolean;
  type?: 'button' | 'submit' | 'reset';
  size?: 'full' | 'auto'
}

export function Button({style, children, onClick, disabled, type = 'button', size = 'auto'}: ButtonProps) {
  return (
    <button
      type={type}
      className={`px-4 py-2 rounded-md
        ${disabled ? "bg-gray-600 text-gray-400 cursor-not-allowed" : 
          style === 'primary' ? "bg-indigo-600 hover:bg-indigo-600/80 font-semibold" :
          style === 'remove' ? "border-2 border-gray-600 hover:text-red-300 hover:border-red-300" :
          "border border-secondary-600 hover:bg-secondary-600/10 text-secondary-600 shadow-[0_0_20px_rgba(124,58,237,0.25)] font-semibold"
        }
        ${size === 'full' ? "w-full" : ""}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}