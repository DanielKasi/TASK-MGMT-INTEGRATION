import { IBranchWorkingDays } from "@/types/types.utils";
import apiRequest from "../apiRequest";

export const branchesAPI = {
	WORKING_DAYS: {
		getAll: async ({ branchId }: { branchId: number }): Promise<IBranchWorkingDays | null> => {
			const response = await apiRequest.get(
				`/institution/branch-working-days/?branch_id=${branchId}`,
			);

			return response.data as IBranchWorkingDays;
		},
		create: async (data: {
			branch_days: Array<{ day_id: number; day_type: "REMOTE" | "PHYSICAL" }>;
		}): Promise<IBranchWorkingDays | null> => {
			const response = await apiRequest.post(`/institution/branch-working-days/`, data);

			return response.data as IBranchWorkingDays;
		},

		update: async (
			branchDaysId: number,
			data: { branch_days: Array<{ day_id: number; day_type: "REMOTE" | "PHYSICAL" }> },
		): Promise<IBranchWorkingDays | null> => {
			const response = await apiRequest.patch(
				`/institution/branch-working-day-detail/${branchDaysId}/`,
				data,
			);

			return response.data as IBranchWorkingDays;
		},
	},
};