"use client";

import type React from "react";

import { useEffect, useState } from "react";
import { ChevronDown } from "lucide-react";

import { Button } from "@/platform/v1/components";
import { Input } from "@/platform/v1/components";
import { ICountry } from "@/types/types.utils";
import { countryAPI } from "@/lib/helpers";

export default function CountrySelect({
	countries: propCountries,
	selectedCountry,
	onCountryChange,
	disabled = false,
	compact = false,
	placeholder = "",
}: {
	countries?: ICountry[];
	selectedCountry: ICountry | null;
	onCountryChange: (country: ICountry | null) => void;
	disabled?: boolean;
	compact?: boolean;
	placeholder?: string;
}) {
	const [isOpen, setIsOpen] = useState(false);
	const [searchTerm, setSearchTerm] = useState("");
	const [countries, setCountries] = useState<ICountry[]>(propCountries || []);
	const [filteredCountries, setFilteredCountries] = useState<ICountry[]>(propCountries || []);

	// Fetch countries if not provided
	useEffect(() => {
		if (!propCountries) {
			countryAPI
				.getAll()
				.then((data) => {
					setCountries(data);
				})
				.catch(() => setCountries([]));
		} else {
			setCountries(propCountries);
		}
	}, [propCountries]);

	// Update filteredCountries when countries or searchTerm changes
	useEffect(() => {
		setFilteredCountries(
			!searchTerm
				? countries
				: countries.filter(
						(country) =>
							country.name.common.toLowerCase().includes(searchTerm.toLowerCase()) ||
							country.cca2.toLowerCase().includes(searchTerm.toLowerCase()),
					),
		);
	}, [searchTerm, countries]);

	const getFlag = (cca2?: string) => {
		if (!cca2 || cca2.length !== 2) return ""; // return empty if invalid

		return String.fromCodePoint(
			...cca2
				.toUpperCase()
				.split("")
				.map((c) => 0x1f1e6 + c.charCodeAt(0) - 65),
		);
	};

	const getCountryCode = (country: ICountry) =>
		country.idd?.root ? `${country.idd.root}${country.idd.suffixes?.[0] || ""}` : "";

	return (
		<div className="relative">
			<Button
				disabled={disabled}
				type="button"
				variant="outline"
				className="w-fit md:w-full h-[48px] rounded-[14px] border justify-between"
				onClick={() => setIsOpen((v) => !v)}
			>
				<span className="flex items-center gap-2 truncate">
					{selectedCountry ? (
						<>
							<span className="text-lg hidden md:!inline">{getFlag(selectedCountry.cca2)}</span>
							{compact ? getCountryCode(selectedCountry) : selectedCountry.name.common}
						</>
					) : compact ? (
						<span className="text-gray-400">+Code</span>
					) : (
						placeholder || "Select country"
					)}
				</span>
				<span className="ml-auto">
					<ChevronDown className="h-4 w-4" />
				</span>
			</Button>
			{isOpen && (
				<div className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-80 overflow-hidden">
					<div className="p-2 border-b border-gray-100">
						<Input
							placeholder="Search countries..."
							disabled={disabled}
							value={searchTerm}
							onChange={(e) => setSearchTerm(e.target.value)}
							className="text-sm border-0 focus-visible:ring-0 focus-visible:ring-offset-0"
						/>
					</div>
					<div className="max-h-60 overflow-y-auto">
						{filteredCountries.length > 0 ? (
							filteredCountries.map((country) => (
								<button
									key={country.cca2}
									type="button"
									onClick={() => {
										onCountryChange(country);
										setIsOpen(false);
										setSearchTerm("");
									}}
									className={`w-full px-3 py-2 text-left hover:bg-gray-50 flex items-center gap-2 ${
										selectedCountry?.cca2 === country.cca2 ? "bg-blue-50 text-blue-600" : ""
									}`}
								>
									<span className="text-lg">{getFlag(country.cca2)}</span>
									{!compact ? (
										<span className="font-medium text-sm">{country.name.common}</span>
									) : (
										<></>
									)}

									<span className="ml-auto text-xs text-gray-400">{country.cca2}</span>
								</button>
							))
						) : (
							<div className="px-3 py-4 text-center text-sm text-gray-500">
								No countries found matching "{searchTerm}"
							</div>
						)}
					</div>
				</div>
			)}
		</div>
	);
}
