"use client";

import { InitialConfigType, LexicalComposer } from "@lexical/react/LexicalComposer";
import { OnChangePlugin } from "@lexical/react/LexicalOnChangePlugin";
import { EditorState, SerializedEditorState } from "lexical";

import { TooltipProvider } from "@/platform/v1/components";

import { nodes } from "./nodes";
import { Plugins } from "./plugins";

// Define editor theme locally
const editorTheme = {
	text: {
		bold: "font-bold",
		italic: "italic",
		underline: "underline",
		strikethrough: "line-through",
		code: "font-mono bg-gray-100 px-1 py-0.5 rounded",
	},
	paragraph: "mb-2",
	heading: {
		h1: "text-2xl font-bold mb-4",
		h2: "text-xl font-bold mb-3",
		h3: "text-lg font-bold mb-2",
	},
	list: {
		nested: {
			listitem: "list-none",
		},
		ol: "list-decimal list-inside mb-2",
		ul: "list-disc list-inside mb-2",
		listitem: "mb-1",
	},
	link: "text-blue-600 underline",
	code: "bg-gray-100 p-2 rounded font-mono text-sm",
	codeHighlight: {
		atrule: "text-purple-600",
		attr: "text-blue-600",
		boolean: "text-red-600",
		builtin: "text-purple-600",
		cdata: "text-gray-600",
		char: "text-green-600",
		class: "text-blue-600",
		"class-name": "text-blue-600",
		comment: "text-gray-500 italic",
		constant: "text-red-600",
		deleted: "text-red-600",
		doctype: "text-gray-600",
		entity: "text-orange-600",
		function: "text-blue-600",
		important: "text-red-600",
		inserted: "text-green-600",
		keyword: "text-purple-600",
		namespace: "text-blue-600",
		number: "text-red-600",
		operator: "text-gray-600",
		prolog: "text-gray-600",
		property: "text-blue-600",
		punctuation: "text-gray-600",
		regex: "text-orange-600",
		selector: "text-blue-600",
		string: "text-green-600",
		symbol: "text-purple-600",
		tag: "text-red-600",
		url: "text-blue-600",
		variable: "text-orange-600",
	},
};

const editorConfig: InitialConfigType = {
	namespace: "Editor",
	theme: editorTheme,
	nodes,
	onError: (error: Error) => {
		console.error(error);
	},
};

export function Editor({
	editorState,
	editorSerializedState,
	onChange,
	onSerializedChange,
}: {
	editorState?: EditorState;
	editorSerializedState?: SerializedEditorState;
	onChange?: (editorState: EditorState) => void;
	onSerializedChange?: (editorSerializedState: SerializedEditorState) => void;
}) {
	return (
		<div className="bg-background overflow-hidden rounded-lg border shadow">
			<LexicalComposer
				initialConfig={{
					...editorConfig,
					...(editorState ? { editorState } : {}),
					...(editorSerializedState ? { editorState: JSON.stringify(editorSerializedState) } : {}),
				}}
			>
				<TooltipProvider>
					<Plugins />

					<OnChangePlugin
						ignoreSelectionChange={true}
						onChange={(editorState) => {
							onChange?.(editorState);
							onSerializedChange?.(editorState.toJSON());
						}}
					/>
				</TooltipProvider>
			</LexicalComposer>
		</div>
	);
}
