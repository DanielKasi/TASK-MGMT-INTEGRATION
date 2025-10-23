"use client";

import React, { useEffect } from "react";
import { useSelector } from "react-redux";
import { useModuleNavigation } from "@/hooks/use-module-navigation";

import { selectPendingRedirect } from "@/store/redirects/selectors-context-aware";
import { selectUser } from "@/store/auth/selectors-context-aware";
import { RedirectPayload } from "@/store/redirects/types";

function buildPathFromRedirect(redirect: RedirectPayload) {
	if (!redirect) return "/";
	const { intent, intent_id } = redirect;

	switch (intent) {
		case "spot_check":
			return `/spot-checks/${intent_id}`;
		default:
			return `/dashboard`;
	}
}

export default function RedirectsWatcher() {
	const pending = useSelector(selectPendingRedirect);
	const user = useSelector(selectUser);
	const router = useModuleNavigation();
	const [hasRedirected, setHasRedirected] = React.useState(false);

	useEffect(() => {
		// console.log("RedirectsWatcher: pending", pending);
		// console.log("RedirectsWatcher: user", user);
		if (hasRedirected) return;
		if (!pending) return;
		if (!user) return;
		const path = buildPathFromRedirect(pending);

		// console.log("\n\n Redirecting to", path);
		router.push(path);
		// window.location.replace(path);
		// router.replace(path);
		// router.push(path);
		setHasRedirected(true);
	}, [pending, user, router]);

	return null;
}
