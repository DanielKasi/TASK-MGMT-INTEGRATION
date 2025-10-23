"use client";

import React, { useState, useEffect } from "react";

import {
	Dialog,
	DialogContent,
	DialogHeader,
	DialogTitle,
	DialogFooter,
} from "@/platform/v1/components";
import { Button } from "@/platform/v1/components";
import { Input } from "@/platform/v1/components";
import { Label } from "@/platform/v1/components";

interface IJobEditor {
	id?: number;
	name: string;
	description?: string | null;
}

interface Props {
	open: boolean;
	departmentName?: string;
	initial?: IJobEditor | null;
	onClose: () => void;
	onSave: (job: IJobEditor) => void;
}

export default function JobEditorDialog({ open, initial, departmentName, onClose, onSave }: Props) {
	const [name, setName] = useState("");
	const [description, setDescription] = useState("");

	useEffect(() => {
		if (open) {
			setName(initial?.name ?? "");
			setDescription(initial?.description ?? "");
		}
	}, [initial, open]);

	const handleSave = () => {
		onSave({
			id: initial?.id ?? 0,
			name: name.trim() || "New Job",
			description: description.trim(),
		});
		onClose();
	};

	return (
		<Dialog
			open={open}
			onOpenChange={(v) => {
				if (!v) onClose();
			}}
		>
			<DialogContent className="sm:max-w-md">
				<DialogHeader>
					<DialogTitle>
						{initial ? "Edit Job Position" : "Add Job Position"} {initial ? "From" : "To"}{" "}
						{departmentName}
					</DialogTitle>
				</DialogHeader>

				<div className="grid gap-2">
					<Label>Job Title</Label>
					<Input
						placeholder="e.g. Software Engineer"
						value={name}
						onChange={(e) => setName(e.target.value)}
					/>
					<Label>Description</Label>
					<Input
						placeholder="Short description (optional)"
						value={description}
						onChange={(e) => setDescription(e.target.value)}
					/>
				</div>

				<DialogFooter className="mt-8 flex justify-end gap-2">
					<Button className="w-full rounded-full" onClick={handleSave}>
						{initial ? "Save" : "Add"}
					</Button>
				</DialogFooter>
			</DialogContent>
		</Dialog>
	);
}
