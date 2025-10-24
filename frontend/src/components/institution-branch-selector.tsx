"use client";

import { useState, useEffect } from "react";
import { ChevronDown } from "lucide-react";
import { useSelector } from "react-redux";
import { useDispatch } from "react-redux";

import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from "@/platform/v1/components";
import {
	selectAttachedInstitutions,
	selectSelectedBranch,
	selectSelectedInstitution,
} from "@/store/auth/selectors-context-aware";
import { setSelectedBranch, setSelectedInstitution } from "@/store/auth/actions";
import { IUserInstitution } from "@/types/other";
import { Branch } from "@/types/branch.types";

interface Institution {
	id: number;
	Institution_name: string;
	branches: Branch[];
}

export function InstitutionBranchSelector() {
	const [Institutions, setInstitutions] = useState<IUserInstitution[]>([]);
	const [displayName, setDisplayName] = useState("Select Institution");
	const InstitutionsAttached = useSelector(selectAttachedInstitutions);
	const selectedInstitution = useSelector(selectSelectedInstitution);
	const selectedBranch = useSelector(selectSelectedBranch);
	const dispatch = useDispatch();
	const mockInstitutions: IUserInstitution[] = [];

	useEffect(() => {
		if (InstitutionsAttached) {
			setInstitutions(InstitutionsAttached);
		} else {
			// Mock data if no Institutions are in localStorage

			setInstitutions(mockInstitutions);
		}
	}, []);

	// Set initial selected Institution and branch if not already set
	useEffect(() => {
		if (InstitutionsAttached.length > 0 && !selectedInstitution) {
			handleInstitutionSelection(InstitutionsAttached[0]);
			if (
				InstitutionsAttached.length &&
				InstitutionsAttached[0].branches &&
				InstitutionsAttached[0].branches.length > 0 &&
				!selectedBranch
			) {
				handleBranchSelection(InstitutionsAttached[0].branches[0]);
			}
		}
	}, [InstitutionsAttached, selectedInstitution, selectedBranch]);

	const handleInstitutionSelection = (Institution: IUserInstitution) => {
		dispatch(setSelectedInstitution(Institution));
	};

	const handleBranchSelection = (branch: Branch) => {
		dispatch(setSelectedBranch(branch));
	};

	// Update display name when Institution or branch changes
	useEffect(() => {
		if (selectedInstitution && selectedBranch) {
			setDisplayName(`${selectedBranch.branch_name}`);
		} else if (selectedInstitution) {
			setDisplayName(selectedInstitution.institution_name);
		} else {
			setDisplayName("Select Institution");
		}
	}, [selectedInstitution, selectedBranch]);

	const handleSelectInstitutionAndBranch = (Institution: IUserInstitution, branch: Branch) => {
		handleInstitutionSelection(Institution);
		handleBranchSelection(branch);

		window.dispatchEvent(new Event("Institution_data_updated"));
	};

	return (
		<DropdownMenu>
			<DropdownMenuTrigger className="bg-white border rounded-full px-4 py-2 flex items-center gap-2 min-w-0 max-w-[200px] w-full">
				<span className="truncate">{displayName}</span>
				<ChevronDown className="h-4 w-4 ml-auto flex-shrink-0" />
			</DropdownMenuTrigger>
			<DropdownMenuContent className="min-w-[200px] max-w-[90vw] rounded-xl z-[150]">
				{InstitutionsAttached.map((Institution) => (
					<div key={Institution.id}>
						{Institution.branches &&
							Institution.branches.map((branch) => (
								<DropdownMenuItem
									key={branch.id}
									className="cursor-pointer"
									onClick={() => handleSelectInstitutionAndBranch(Institution, branch)}
								>
									{branch.branch_name}
									{selectedBranch?.id === branch.id && <span className="ml-auto">✓</span>}
								</DropdownMenuItem>
							))}
						{InstitutionsAttached.length > 1 && <DropdownMenuSeparator />}
					</div>
				))}
			</DropdownMenuContent>
		</DropdownMenu>
	);
}
