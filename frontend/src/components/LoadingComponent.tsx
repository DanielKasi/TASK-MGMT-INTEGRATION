"use client";

import { ReactNode, useState, useEffect } from "react";
import { Skeleton } from "./ui/skeleton";

type Props<T> = {
	initialData: T;
	fetchData: () => Promise<T>;
	content: (data: T) => ReactNode;
};

export default function LoadingComponent<T>({ initialData, fetchData, content }: Props<T>) {
	const [data, setData] = useState<T>(initialData);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string>("");

	useEffect(() => {
		async function load() {
			try {
				const result = await fetchData();

				setData(result as T);
			} catch (err) {
				setError(err instanceof Error ? err.message : "Failed to fetch data");
			} finally {
				setLoading(false);
			}
		}

		load();
	}, []);

	if (loading) {
		return (
			<div className="flex items-center justify-center min-h-screen">
				{/* <Loader2 className="h-8 w-8 animate-spin" /> */}
				<span className="ml-2">Loading...</span>
			</div>
		);
	}

	if (error) {
		return (

			<>
			<div className="gap-6">
						<div
							className={`space-y-6`}
						>
							<Skeleton className="h-48 sm:h-56 md:h-64 w-full bg-gray-200" />
							<Skeleton className="h-48 sm:h-56 md:h-64 w-full bg-gray-200" />
							<Skeleton className="h-40 sm:h-44 md:h-48 w-full bg-gray-200 mt-4 md:mt-8" />
						</div>
					</div>
			</>

			// <div className="flex items-center justify-center min-h-screen">
			// 	<div className="text-center">
			// 		{/* <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" /> */}
			// 		<h2 className="text-xl font-semibold mb-2">Error loading component</h2>
			// 		<p className="text-muted-foreground">{error}</p>
			// 	</div>
			// </div>
		);
	}

	if (!data) return null;

	return <>{content(data)}</>;
}
