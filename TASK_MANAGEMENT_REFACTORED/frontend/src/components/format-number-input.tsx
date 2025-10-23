"use client";

import type { InputHTMLAttributes } from "react";

import { useState } from "react";

import { Input } from "@/platform/v1/components";

interface FormatNumberInputProps
	extends Omit<InputHTMLAttributes<HTMLInputElement>, "onChange" | "value"> {
	value?: string;
	onChange?: (formatted: string, numericValue: number) => void;
}

export default function FormatNumberInput({
	value = "",
	onChange,
	...props
}: FormatNumberInputProps) {
	const [inputValue, setInputValue] = useState<string>(value);

	const formatNumber = (num: string) => {
		if (!num) return "";

		const cleanNum = num.replace(/[^\d.]/g, "");
		const [integer, decimal] = cleanNum.split(".");

		const formattedInt = integer ? integer.replace(/\B(?=(\d{3})+(?!\d))/g, ",") : "";

		return decimal !== undefined ? `${formattedInt}.${decimal}` : formattedInt;
	};

	const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		const rawValue = e.target.value;
		const formatted = formatNumber(rawValue);

		setInputValue(formatted);

		const numericValue = Number(rawValue.replace(/,/g, ""));

		if (onChange) {
			onChange(formatted, numericValue);
		}
	};

	return <Input {...props} type="text" value={inputValue} onChange={handleChange} />;
}
