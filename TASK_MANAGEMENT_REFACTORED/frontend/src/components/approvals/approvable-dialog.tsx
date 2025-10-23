"use client";

import {
	Dialog,
	DialogContent,
	DialogHeader,
	DialogTitle,
	DialogDescription,
} from "@/platform/v1/components";
import { ApprovalWorkflow } from "./approval-workflow";
import type { Approval, ApprovableEntityStatus } from "@/types/approvals.types";
import type { ReactNode } from "react";

interface ApprovableDialogProps {
	isOpen: boolean;
	onOpenChange: (open: boolean) => void;
	title: string;
	description?: string;
	children: ReactNode; // Main content of the dialog (e.g., details form)
	approvals?: Approval[];
	instanceApprovalStatus?: ApprovableEntityStatus;
	onRefresh?: () => void;
	className?: string;
}

export function ApprovableDialog({
	isOpen,
	onOpenChange,
	title,
	description,
	children,
	approvals,
	instanceApprovalStatus,
	onRefresh,
	className = "",
}: ApprovableDialogProps) {
	return (
		<Dialog open={isOpen} onOpenChange={onOpenChange}>
			<DialogContent
				className={`sm:max-w-[700px] md:w-[95vw] sm:w-full rounded-2xl border-0 shadow-2xl ${className}`}
			>
				<DialogHeader className="space-y-3 pb-6 border-b border-gray-100">
					<DialogTitle className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-900">
						{title}
					</DialogTitle>
					{description && (
						<DialogDescription className="text-sm sm:text-base text-gray-600">
							{description}
						</DialogDescription>
					)}
				</DialogHeader>

				<div className="flex flex-col gap-6 py-4 sm:py-6 overflow-y-auto max-h-[70vh]">
					{/* Main content */}
					<div className="space-y-6">{children}</div>

					{/* Approval Workflow - Conditionally rendered and constrained like in details views */}
					{approvals && approvals.length > 0 && instanceApprovalStatus !== "active" && (
						<div className="gap-3">
							<ApprovalWorkflow
								approvals={approvals}
								instance_approval_status={instanceApprovalStatus}
								onRefresh={onRefresh}
							/>
						</div>
					)}
				</div>
			</DialogContent>
		</Dialog>
	);
}
