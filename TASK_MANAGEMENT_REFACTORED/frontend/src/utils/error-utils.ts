import { AxiosError } from "axios";

import { CUSTOM_CODES } from "@/constants";
import { AuthError } from "@/store/auth/reducer";

export const getAuthError = (error: any): AuthError => {
	if (error instanceof AxiosError) {
		const errorData = error.response?.data;

		return {
			customCode: errorData["custom_code"] as CUSTOM_CODES || CUSTOM_CODES.OTHER,
			message: errorData["message"] || errorData["detail"] || errorData["error"] || "Unkown error",
		};
	}
	return { customCode: CUSTOM_CODES.OTHER, message: "Unkown error" };
};
