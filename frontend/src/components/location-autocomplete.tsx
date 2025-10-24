"use client";

import { useState, useEffect, useRef } from "react";
import { Check, ChevronsUpDown, MapPin } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/platform/v1/components";
import {
	Command,
	CommandEmpty,
	CommandGroup,
	CommandInput,
	CommandItem,
	CommandList,
} from "@/platform/v1/components";
import { Popover, PopoverContent, PopoverTrigger } from "@/platform/v1/components";
import { Spinner } from "@/components/ui/spinner";
import { ScrollArea } from "@/platform/v1/components";

interface LocationOption {
	value: string;
	label: string;
	address: string;
}

interface LocationAutocompleteProps {
	value: string;
	onChange: (value: string) => void;
	placeholder?: string;
	className?: string;
	showCurrentLocationButton?: boolean;
	onCoordinatesChange?: (lat: string, lon: string) => void;
}

export function LocationAutocomplete({
	value,
	onChange,
	onCoordinatesChange,
	placeholder = "Search for a location...",
	className,
	showCurrentLocationButton = true,
}: LocationAutocompleteProps) {
	const [open, setOpen] = useState(false);
	const [inputValue, setInputValue] = useState(value);
	const [options, setOptions] = useState<LocationOption[]>([]);
	const [loading, setLoading] = useState(false);
	const [gettingCurrentLocation, setGettingCurrentLocation] = useState(false);
	const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

	useEffect(() => {
		// Update input value when external value changes
		setInputValue(value);
	}, [value]);

	const fetchLocations = async (query: string) => {
		if (!query || query.length < 2) {
			setOptions([]);

			return;
		}

		setLoading(true);
		try {
			const response = await fetch(
				`https://api.geoapify.com/v1/geocode/autocomplete?text=${encodeURIComponent(
					query,
				)}&apiKey=12a8608da7914f4c96cbbc76c7ca954c&limit=5`,
			);

			if (!response.ok) {
				throw new Error("Failed to fetch locations");
			}

			const data = await response.json();

			if (data.features && data.features.length > 0) {
				const locationOptions = data.features.map((feature: any) => {
					const properties = feature.properties;
					const formattedAddress = properties.formatted;

					return {
						value: formattedAddress,
						label: properties.name || properties.street || formattedAddress.split(",")[0],
						address: formattedAddress,
					};
				});

				setOptions(locationOptions);
			} else {
				setOptions([]);
			}
		} catch (error) {
			// console.log("Error fetching location suggestions:", error);
			setOptions([]);
		} finally {
			setLoading(false);
		}
	};

	const handleInputChange = (value: string) => {
		setInputValue(value);

		// Debounce API calls
		if (debounceTimerRef.current) {
			clearTimeout(debounceTimerRef.current);
		}

		debounceTimerRef.current = setTimeout(() => {
			fetchLocations(value);
		}, 300);
	};

	const handleSelectLocation = async (location: string) => {
		onChange(location);
		setInputValue(location);
		setOpen(false);

		try {
			const response = await fetch(
				`https://api.geoapify.com/v1/geocode/search?text=${encodeURIComponent(
					location,
				)}&apiKey=12a8608da7914f4c96cbbc76c7ca954c&limit=1`,
			);

			// console.log("Response from Geoapify:", response);

			if (!response.ok) throw new Error("Failed to get coordinates");

			const data = await response.json();

			if (data.features && data.features.length > 0) {
				const coords = data.features[0].geometry.coordinates;
				const [lon, lat] = coords;

				onCoordinatesChange?.(lat.toString(), lon.toString());
			}
		} catch (error) {
			// console.log("Failed to get coordinates from selected location:", error);
		}
	};

	return (
		<div className="w-full">
			<Popover open={open} onOpenChange={setOpen}>
				<PopoverTrigger asChild>
					<Button
						aria-expanded={open}
						className={cn("w-full justify-between text-left", className)}
						role="combobox"
						title={value} // Add title attribute for tooltip on hover
						variant="outline"
					>
						{value ? (
							<div className="flex items-center w-full">
								<MapPin className="mr-2 h-4 w-4 shrink-0 text-muted-foreground" />
								<span className="truncate">{value}</span>
							</div>
						) : (
							<span className="text-muted-foreground">{placeholder}</span>
						)}
						<ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
					</Button>
				</PopoverTrigger>
				<PopoverContent align="start" className="w-[350px] p-0" side="bottom">
					<Command>
						<CommandInput
							placeholder={placeholder}
							value={inputValue}
							onValueChange={handleInputChange}
						/>
						<CommandList>
							{loading && (
								<div className="flex items-center justify-center py-6">
									<Spinner className="h-4 w-4 mr-2" />
									<span className="text-sm text-muted-foreground">Searching locations...</span>
								</div>
							)}
							<CommandEmpty>
								{inputValue.length > 0 ? (
									<div className="py-6 text-center">
										<p className="text-sm text-muted-foreground">
											No locations found for "{inputValue}"
										</p>
									</div>
								) : (
									<div className="py-6 text-center">
										<p className="text-sm text-muted-foreground">Type to search for locations</p>
									</div>
								)}
							</CommandEmpty>
							<CommandGroup>
								<ScrollArea className="max-h-[300px]">
									{options.map((option) => (
										<CommandItem
											key={option.value}
											className="flex flex-col items-start py-3"
											value={option.value}
											onSelect={() => handleSelectLocation(option.value)}
										>
											<div className="flex items-start gap-2 w-full">
												<Check
													className={cn(
														"mt-1 h-4 w-4 flex-shrink-0",
														value === option.value ? "opacity-100" : "opacity-0",
													)}
												/>
												<div className="flex flex-col overflow-hidden w-full">
													<span className="font-medium">{option.label}</span>
													<span className="text-xs text-muted-foreground break-words">
														{option.address}
													</span>
												</div>
											</div>
										</CommandItem>
									))}
								</ScrollArea>
							</CommandGroup>
						</CommandList>
					</Command>
				</PopoverContent>
			</Popover>
		</div>
	);
}
