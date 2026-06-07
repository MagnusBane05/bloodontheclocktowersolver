import React from 'react';
import { SelectOption } from './types';
import { Toggle } from '../Toggle';

interface FieldProps {
  label?: string;
  htmlFor?: string;
  children: React.ReactNode;
  error?: string;
}

export function Field({ label, htmlFor, children, error }: FieldProps): JSX.Element {
  return (
    <div className="space-y-2 w-full">
      {label && (
        <label htmlFor={htmlFor} className="block text-sm font-medium">
          {label}
        </label>
      )}
      {children}
      {error && <p className="text-sm text-red-300">{error}</p>}
    </div>
  );
}

interface SelectFieldProps {
  id: string;
  label: string;
  value?: string | number | null;
  options: SelectOption[];
  placeholder: string;
  onChange: (value: string | number | null) => void;
  error?: string;
  disabled?: boolean;
}

export function SelectField({
  id,
  label,
  value,
  options,
  placeholder,
  onChange,
  error,
  disabled,
}: SelectFieldProps): JSX.Element {
  return (
    <Field label={label} htmlFor={id} error={error}>
      <select
        id={id}
        value={value ?? ''}
        disabled={disabled}
        onChange={(e) =>
          onChange(e.target.value === '' ? null : isNaN(Number(e.target.value)) ? e.target.value : Number(e.target.value))
        }
        className={`w-full min-h-[42px] p-2 bg-gray-700 border border-gray-600 hover:border-gray-500 rounded-md text-white capitalize 
                  focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20 ${
          disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
        }`}
      >
        <option value="">{placeholder}</option>
        {options.map((option) => (
          <option key={`${option.value}-${option.label}`} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </Field>
  );
}

interface NumberFieldProps {
  id: string;
  label: string;
  value?: number | null;
  min?: number;
  max?: number;
  placeholder?: string;
  onChange: (value: number | null) => void;
  error?: string;
}

export function NumberField({ id, label, value, min, max, placeholder, onChange, error }: NumberFieldProps): JSX.Element {
  return (
    <Field label={label} htmlFor={id} error={error}>
      <input
        id={id}
        type="number"
        value={value ?? ''}
        min={min}
        max={max}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value === '' ? null : parseInt(e.target.value, 10))}
        className="w-full min-w-12 p-2 bg-gray-700 border border-gray-600 hover:border-gray-500 rounded-md text-white 
                  focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20"
      />
    </Field>
  );
}

interface CheckboxFieldProps {
  id: string;
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
  error?: string;
}

export function CheckboxField({ id, label, checked, onChange, error }: CheckboxFieldProps): JSX.Element {
  return (
    <Field htmlFor={id} error={error}>
      <div className="flex items-center gap-2">
        <input
          id={id}
          type="checkbox"
          checked={checked ?? false}
          onChange={(e) => onChange(e.target.checked)}
          className="h-4 w-4 rounded border-gray-700 bg-gray-900 text-indigo-500 focus:ring-indigo-500"
        />
        <label htmlFor={id} className="text-sm text-white cursor-pointer select-none">
          {label}
        </label>
      </div>
    </Field>
  );
}

export function ToggleField({ id, label, checked, onChange, error }: CheckboxFieldProps): JSX.Element {
  return (
    <Field htmlFor={id} error={error}>
      <label htmlFor={id} className="inline-flex items-center gap-2 cursor-pointer select-none">
        <Toggle 
          checked={checked ?? false}
          onChange={onChange}
          id={id}
        />
        <span className="text-sm text-white">{label}</span>
      </label>
    </Field>
  );
}

interface ButtonFieldProps {
  label: string;
  value: number | null;
  playerNames?: string[];
  onClick: () => void;
  error?: string;
  disabled?: boolean;
}

export function ButtonField({
  label,
  value,
  playerNames,
  onClick,
  error,
  disabled = false,
}: ButtonFieldProps): JSX.Element {

  const playerLabel =
    value !== null
      ? playerNames?.[value] ?? `Player ${value + 1}`
      : 'Select player...';

  return (
    <Field label={label} error={error}>
      <button
        type="button"
        onClick={onClick}
        disabled={disabled}
        className={`w-full min-h-[42px] p-2 rounded-md transition text-left font-medium ${
          disabled
            ? 'opacity-50 cursor-not-allowed bg-gray-600 text-gray-400'
            : 'bg-gray-700 border border-gray-600 text-gray-100 placeholder:text-gray-500' +
            'transition-all hover:border-gray-500 focus:outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20'
        }`}
      >
        {playerLabel}
      </button>
    </Field>
  );
}

interface ReadOnlyFieldProps {
  label: string;
  error?: string;
  value: string;
}

export function ReadOnlyField({
  label,
  error,
  value,
}: ReadOnlyFieldProps) {
  return (
    <Field label={label} error={error}>
      <div className="min-h-[42px] p-2 opacity-50 cursor-text bg-gray-600 rounded-md capitalize">{value}</div>
    </Field>
  );
}