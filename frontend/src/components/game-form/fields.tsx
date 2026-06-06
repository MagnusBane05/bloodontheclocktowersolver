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
    <div className="space-y-2">
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
        className={`w-full min-h-[42px] p-2 bg-gray-600 border border-gray-500 rounded-md text-white capitalize ${
          disabled ? 'opacity-50 cursor-not-allowed' : ''
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
        className="w-full min-w-12 p-2 bg-gray-600 border border-gray-500 rounded-md text-white"
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
          className="h-4 w-4 rounded border-gray-500 bg-gray-700 text-indigo-500 focus:ring-indigo-500"
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
