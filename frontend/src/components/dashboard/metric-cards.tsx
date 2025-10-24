"use client";

import { Icon } from "@iconify/react";
import Link from "next/link";

import { Card, CardContent } from "@/platform/v1/components";
import { IBasicDasboardDataCounts } from "@/types/types.utils";
import { useEffect, useState } from "react";
import { PROJECTS_API, PROJECTS_TASKS_API } from "@/lib/utils";

interface MetricCardsProps {
	data?: IBasicDasboardDataCounts;
	// onRefresh?: () => void;
	// loading?: boolean;
}

export function MetricCards({ data }: MetricCardsProps) {

	const [projectsCount, setProjectsCount] = useState(0);
	const [tasksCount, setTasksCount] = useState(0);

	useEffect(() => {
		fetchProjectsMetrics();
		fetchTasksMetrics();
	}, []);

	const fetchProjectsMetrics = async () => {
		try {
			const response = await PROJECTS_API.getPaginatedProjects({});
			setProjectsCount(response.count);
		} catch (error) {
			setProjectsCount(0);
		}
	}

	const fetchTasksMetrics = async () => {
		try {
			const response = await PROJECTS_TASKS_API.getPaginatedTasks({});
			setTasksCount(response.count);
		} catch (error) {
			setTasksCount(0);
		}
	}

	const metrics = [
		{
			title: "Total Tasks",
			value: tasksCount,
			icon: "hugeicons:task-edit-01",
			bgColor: "bg-blue-100",
			iconColor: "text-blue-600",
			link: "/projects",
		},
		{
			title: "Projects",
			value: projectsCount,
			icon: "hugeicons:gitbook",
			bgColor: "bg-blue-100",
			iconColor: "text-blue-600",
			link: "/projects",
		},
	];

	return (
		<div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-white rounded-lg md:rounded-xl">
			{metrics.map((metric, index) => (
				<div key={index} className="flex w-full items-center justify-start gap-1">
					<Card className="bg-transparent w-full min-w-max shadow-none border-none">
						<CardContent className="p-6">
							<div className="flex items-center justify-between">
								<div className="flex items-center gap-3">
									<div
										className={`w-12 h-12 ${metric.bgColor} rounded-xl p-2 flex items-center justify-center`}
									>
										<Icon icon={metric.icon} className={`!w-9 !h-9 ${metric.iconColor}`} />
									</div>
									<div>
										<p className="text-sm text-gray-600">{metric.title}</p>
										<p className="text-2xl font-bold">{metric.value}</p>
									</div>
								</div>
								{metric.link && (
									<Link
										href={metric.link}
										className="!rounded-full aspect-square hover:bg-gray-100 border border-black/20 p-2 transition-colors"
									>
										<Icon icon="hugeicons:arrow-up-right-01" className="!w-6 !h-6" />
									</Link>
								)}
							</div>
						</CardContent>
					</Card>
					{index <= metrics.length - 2 && (
						<div className="w-[2px] h-full bg-gray-200 rounded-full" />
					)}
				</div>
			))}
		</div>
	);
}
