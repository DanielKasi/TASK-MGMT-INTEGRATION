import type { ApprovableEntityStatus, Approval, ApprovalTask, IBaseApprovable } from "@/types/approvals.types";
import { ICustomField, IProjectDashboard, IProjectStatus, IProjectTaskStatuses, IProjectTaskStatusFormData, ITaskPriority, ITaskStandAloneStatuses, ITaskStandAloneStatusFormData, ITaskStatus} from "./project.type";
import { Branch } from "./branch.types";
import { IUserInstitution } from "./other";
import { IUser, Role, UserProfile } from "./user.types";

export type ContextType = "employee" | "department" | "job_position";
export type CalculationMethod = "fixed" | "percentage";

export interface ContextItem {
	id: number;
	name: string;
	description?: string;
}

export interface IInstitution {
	id: number;
	institution_email: string;
	institution_name: string;
	first_phone_number: string;
	second_phone_number?: string | null;
	institution_logo?: string | null; // ImageField serialized as URL or null
	institution_owner_id: number; // ForeignKey as ID
	theme_Color?: string | null;
	location?: string | null;
	latitude?: number | null;
	longitude?: number | null;
	approval_status: string;
	approval_status_display: string;
	approval_date?: string | null; // ISO date
	documents: IInstitutionDocument[]; // Embedded serializer
	document_files?: File[]; // Write-only field
	document_titles?: string[]; // Write-only field
}

export interface IInstitutionDocument {
	id: number;
	title: string;
	fileUrl: string; // Adjust based on the serializer output
}

// Extended form data that includes interview stages setup

export interface ICompanyEmail {
	id: number;
	employee: number;
	email: string;
	provider: string;
	status: string;
}

export interface IEmployee {
	id: number;
	date_of_birth: string;
	user: IUser | null;
	roles: Role[];
	employee_working_days: any | null;
	educations: IEducation[];
	next_of_kin: INextOfKin[];
	children: IChild[];
	company_email: ICompanyEmail | null;
	spouse: {
		name: string;
		phone_number: string;
		date_of_birth: string;
	} | null;
	created_at: string;
	updated_at: string;
	deleted_at: string | null;
	is_active: boolean;
	employee_id: string;
	email: string;
	name: string | null;
	phone_number: string;
	gender: IGender;
	date_of_joining: string;
	address: string;
	country: string;
	nin: string;
	nssf_no: string;
	tin: string;
	skills: string;
	marital_status: IMaritalStatus;
	has_children: boolean;
	employee_profile_picture: string | null;
	salary: string;
	position: {
		id: number;
		name: string;
		department_id: number;
	};
	department: IDepartment;
	payroll_branch: Branch | null;
}


export interface DashboardError {
	error: string;
}

export type DashboardResponse = IProjectDashboard | DashboardError;
export interface IAttendanceDashboard {
	total_attendance_records: number;
	attendance_by_status: Array<{
		status: string;
		count: number;
	}>;
	average_overtime_hours: number;
	average_late_minutes: number;
	average_early_checkout_minutes: number;
	spot_check_response_rate: number;
	spot_checks_by_status: Array<{
		status: string;
		count: number;
	}>;
	attendance_over_time: Array<{
		month: string;
		count: number;
	}>;
}

export interface IFeedbackField {
	label: string;
	type: "text" | "rating" | "checkbox";
	required: boolean;
	options?: number[] | string[];
}


export interface User {
	email: string;
	fullname: string;
	password?: string;
	roles_ids?: number[];
	permissions?: string;
}

export type IGender = "male" | "female" | "other";
export type IMaritalStatus = "single" | "married" | "divorced" | "widowed";

// Base interfaces for nested objects
export interface IChild {
	id: string;
	name: string;
	gender: IGender;
	date_of_birth: string;
}

export interface INextOfKin {
	id: string;
	name: string;
	phone_number: string;
	phone_number_country_code?: string;
	relationship: string;
	address: string;
}

export interface IEducation {
	id: string;
	name: string;
	institution: string;
	year: string;
	qualification: IQualificationAward | null;
}

export interface IEmployeeEducationFormData {
	id: string;
	name: string;
	institution: string;
	year: string;
	qualification_id: number;
}

export interface IQualificationAward {
	id: number;
	name: string;
	description: string;
}


export interface IEmployeeBankAccountFormData {
	id?: string;
	bank_id: number;
	account_number: string;
	account_name: string;
}

// Main employee form interface for backend API
export interface IEmployeeFormData {
	user: Partial<IUser>;
	id?: number;
	email: string;
	company_email?: string;
	gender: "male" | "female" | "other";
	phone_number: string;
	phone_number_country_code?: string;
	position: number;
	department: number;
	work_type: number;
	employee_type: number;
	date_of_birth: string;
	date_of_joining: string;
	address: string;
	country: string;
	nin: string;
	tin: string;
	nssf_no: string;
	salary: number;
	is_active: boolean;
	skills: string;
	marital_status: IMaritalStatus;
	employee_profile_picture?: File | null;
	selected_branches: number[];
	has_children: boolean;

	// Nested arrays and objects
	children: IChild[];
	next_of_kin: INextOfKin[];
	educations: IEmployeeEducationFormData[];
	bank_accounts: IEmployeeBankAccountFormData[];

	// Legacy fields for backward compatibility
	emergency_contact_name?: string;
	emergency_contact_phone?: string;
	emergency_contact_relationship?: string;
	bank?: string;
	bank_account_number?: string;
	payroll_branch?: number | null;
}

// Interface for local form state management
export interface ICreateEmployeeForm {
	// Basic Information
	fullname: string;
	email: string;
	company_email?: string;
	phone_number: string;
	phone_number_country_code?: string;
	gender: "male" | "female" | "other";
	date_of_birth: string;
	address: string;
	country: string;
	nin: string;
	marital_status: IMaritalStatus;

	// Work Information
	position: number;
	department: number;
	work_type: number;
	employee_type: number;
	date_of_joining: string;
	skills: string;
	selected_branches: number[];
	is_active: boolean;
	has_children: boolean;

	// Financial Information
	tin: string;
	nssf_no: string;
	salary: number;

	// Nested structures
	children: IChild[];
	next_of_kin: INextOfKin[];
	educations: IEducation[];
	bank_accounts: IEmployeeBankAccountFormData[];
}

// Form step types
export type EmployeeFormStep = "personal" | "work" | "financial";

export type RequiredEmployeeFields = Pick<
	IEmployeeFormData,
	| "user"
	| "email"
	| "phone_number"
	| "position"
	| "work_type"
	| "employee_type"
	| "date_of_birth"
	| "selected_branches"
>;

export interface IRoleResponse {
	id: number;
	name: string;
	description: string;
	institution: number;
	permissions_details: string;
}


export interface IRole {
	id: number;
	name: string;
	description: string;
	institution: number; // ForeignKey as ID
	permissions_details: string[]; // List of permission codes
}
export interface IRoleFormData {
	name: string;
	description: string;
	institution: number; // ForeignKey as ID
	permissions_details: string[]; // List of permission codes
}

export interface IAttendance {
	id: number;
	employee: IEmployee;
	check_in_time: string;
	check_out_time: string | null;
	check_in_latitude?: number;
	check_in_longitude?: number;
	check_out_latitude?: number;
	check_out_longitude?: number;
	status: string;
	date: string;
	overtime_hours: string;
}

export interface IAttendanceFormData {
	employee: number;
	check_in_time: string;
	check_in_longitude?: number;
	check_in_latitude?: number;
	check_out_longitude?: number;
	check_out_latitude?: number;
	check_out_time?: string | null;
	status: string;
	date?: string;
	overtime_hours?: string;
}


export interface BranchSummary {
	id: number;
	name: string;
	location: string;
	is_default?: boolean;
	attached_date?: string;
}


export interface EmployeeBranchSummary {
	branches: BranchSummary[];
	default_branch: BranchSummary | null;
}

export interface UserBranch {
	id: number;
	user_id: number;
	user_email: string;
	branch_id: number;
	branch_name: string;
	is_default: boolean;
	created_at: string;
}

export interface AttachBranchesPayload {
	employee_id: number;
	branches: {
		branch_id: number;
		is_default?: boolean;
	}[];
}

export interface SetDefaultBranchPayload {
	branch_id: number;
}


interface IPlaceholder {
	value: string;
}

interface IPlaceholders {
	[key: string]: IPlaceholder;
}

export interface IGeneratedDocumentTemplate {
	id: number;
	template_id: number;
	placeholders: IPlaceholders | null;
}

export interface ICountry {
	name: { common: string };
	cca2: string;
	idd?: { root?: string; suffixes?: string[] };
}

export type ApprovalStepApprover = {
	id: string;
	approver_user: UserProfile;
};

export interface ITask {
	id: string;
	step: ApprovalStep;
	status: string;
	comment: string;
	approved_by: UserProfile | null;
}

export type ApprovalStep = {
	id: string;
	step_name: string;
	roles: string[];
	roles_details: {
		name: string;
		id: string;
	}[];
	approvers?: string[];
	approvers_details?: ApprovalStepApprover[];
	shop: string;
	action: string;
	action_details: {
		id: string;
		code: string;
		label: string;
		category: {
			code: string;
			label: string;
		};
	};
	level: number;
};

// Termination Types
export type TerminationInitiationStatus = "submitted" | "under_review" | "approved" | "rejected";
export type SeparationStatus = "planned" | "completed" | "cancelled";

export interface IEmployeeSeparation {
	id: number;
	effective_date: string;
	additional_notes: string | null;
	separation_status: SeparationStatus;
	employee_separation_type: number;
	employee: IEmployee;
	initiated_by: UserProfile;
}

export interface ITermination {
	id: number;
	separation: IEmployeeSeparation;
	termination_letter: string | null;
	comments: string;
	last_working_day: string;
	initiation_status: TerminationInitiationStatus;
	created_at: string;
	updated_at: string;
}

export interface ITerminationFormData {
	employee_id: number;
	termination_letter?: File | null;
	comments: string;
	last_working_day: string;
}




export interface IPaginatedResponse<T> {
	count: number;
	next: string | null;
	previous: string | null;
	results: T[];
}


export interface ISystemWorkingDay {
	id: number;
	day_code: string;
	day_name: string;
	level: number;
}

// Institution Working Days interface
export interface IInstitutionWorkingDays {
	id: number;
	institution: number;
	days: ISystemWorkingDay[];
	created_by: number | null;
	created_at: string;
	updated_by: number | null;
	updated_at: string;
}

// Form data for creating/updating institution working days
export interface IWorkingDaysFormData {
	days: number[];
}

export interface ITax {
	id: number;
	institution: number;
	tax_name: string;
	tax_status: boolean;
	created_by: number;
	created_at: string;
	updated_by: number;
	updated_at: string;
}
export interface DashboardCategory {
	count: number;
	tasks: ApprovalTask[];
}

export interface ApprovalTasksDashboardResponse {
	incoming: DashboardCategory;
	open: DashboardCategory;
	critical: DashboardCategory;
	expired: DashboardCategory;
	outgoing: DashboardCategory;
}

export type TaskType = "incoming" | "open" | "critical" | "expired" | "outgoing";

export interface ChangePasswordData {
	old_password: string;
	new_password: string;
	new_password_confirm: string;
}


export interface IPublicHolidayFormData {
	institution: number;
	title: string;
	date: string;
}

export interface IEvent {
	id: number;
	institution: number;
	title: string;
	description: string;
	date: string;
	target_audience: "all" | "department" | "individual" | "specific_employees";
	event_mode: "physical" | "online" | "hybrid";
	department?: string;
	specific_employees?: string[];
	created_at: string;
	updated_at: string;
	created_by?: number;
	updated_by?: number;
}

export interface IPublicHoliday {
	id: number;
	institution: number;
	title: string;
	date: string;
	created_at: string;
	updated_at: string;
}

export interface IEventOccurrence {
	id: number;
	event: IEvent;
	date: string;
}

export interface ICalendar {
	id: number;
	institution: number;
	year: number;
	public_holidays: IPublicHoliday[];
	event_occurrences: IEventOccurrence[];
	created_at: string;
	updated_at: string;
}

export interface IEmployeeTaxFormData {
	target_departments?: number[];
	target_job_positions?: number[];
	target_employees?: number[];
	effective_from: string;
	effective_to?: string;
	institution_tax: number | string;
}

export interface ICalendarEvent {
	institution: number | IInstitution;
	year: string;
	public_holidays: number[] | IPublicHoliday[];
	events: number[] | IEvent[];
	created_at: string;
	updated_at: string;
}

export type IBasicDasboardDataCounts = {
	employee_count: number;
	department_count: number;
	on_leave_count: number;
};

export interface IInstitutionAnalytics {
	basic_counts: IBasicDasboardDataCounts;
	payroll_summary: {
		current: {
			month: string; // e.g. "01" through "12"
			payroll: number;
		}[];
		past: {
			total: number;
		};
	};
	employees_per_department: {
		dept_name: string;
		count: number;
		year: number;
	}[];
	gender_distribution: {
		employees_count: number;
		male: number;
		female: number;
		other: number;
	};
	payroll_by_department: {
		dept: string;
		payroll: number;
	}[];
}

export interface IKYCDocument {
	id: number;
	institution: number;
	document_title: string;
	document_file: string;
	created_at: string;
	updated_at: string;
}
export type ISpotCheckInitiator = "system" | "user";

export interface ISpotCheck {
	id: number;
	employee: IEmployee;
	created_at: string;
	updated_at: string;
	responded_at: string | null;
	address: string;
	latitude: number | null;
	longitude: number | null;
	initiated_by: ISpotCheckInitiator;
	spotcheck_time: string | null;
	status: ISpotCheckStatus;
	duration: string | null;
	notes: string | null;
}

export interface ISpotCheckFormData {
	employee: number;
	latitude: number;
	longitude: number;
	initiated_by: ISpotCheckInitiator;
	notes: string;
}

export interface ISpotCheckStatus {
	id: number;
	code: string;
	status_name: string;
	description: string;
}

export interface ILocation {
	latitude: number;
	longitude: number;
}

export interface IInstitutionPenaltyConfig {
	id: number;
	institution: number;
	penalty_type: string;
	penalty_value: number;
	penalty_value_type: string;
	percentage: number | null;
	created_at: string;
	updated_at: string;
}

export interface IInstitutionPenaltyConfigFormData {
	penalty_type: string;
	penalty_value: number;
	penalty_value_type: string;
	percentage?: number;
	institution: number;
}

export interface IBranchPenaltyConfig {
	id: number;
	branch: number;
	penalty_type: string;
	penalty_value: number;
	penalty_value_type: string;
	percentage: number | null;
	created_at: string;
	updated_at: string;
}

export interface IBranchPenaltyConfigFormData {
	branch: number;
	penalty_type: string;
	penalty_value: number;
	penalty_value_type: string;
	percentage?: number;
}

export interface IBranchLocationComparisonConfig {
	id: number;
	branch: number;
	branch_name: string;

	radius_in_meters: number;
	created_at: string;
	updated_at: string;
}

export interface IBranchLocationComparisonConfigFormData {
	branch: number;
	radius_in_meters: number;
}

export type IEmployeeShiftContext = "REQUEST" | "ASSIGNMENT" | "ALLOCATION";
export type IEmployeeShiftStatus = "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED" | "ASSIGNED";

export interface IBranchDay {
	id: number;
	day_id: number;
	day_name: string;
	day_type: "PHYSICAL" | "REMOTE";
}

export interface IBranchWorkingDays {
	id: number;
	branch: Branch;
	branch_days: IBranchDay[];
}


export type IProjectTaskStatus = "not_started" | "in_progress" | "completed" | "on_hold";
export type IProjectTaskPriority = "low" | "medium" | "high" | "urgent";

export interface ITaskTimeSheet {
	id: number;
	task: number;
	start_time: string | null;
	end_time: string | null;
	time_spent: string | null;
	notes: string;
	created_at: string;
	updated_at: string;
	created_by: number | null;
	updated_by: number | null;
}

export type TaskStatusSummary = Pick<ITaskStatus, 'id' | 'name' | 'color_code'>;
export type TaskPrioritySummary = Pick<ITaskPriority, 'id' | 'name' | 'weight'> & { color: string };


export interface IProjectTask extends IBaseApprovable {
	id: number;
	task_name: string;
	project: number | { id: number; project_name: string } | null;
	task_status: TaskStatusSummary;
	priority: TaskPrioritySummary | null;
	created_at: string;
	updated_at: string;
	deleted_at: string | null;
	is_active: boolean;
	description: string;
	start_date: string | null;
	end_date: string | null;
	completion_date: string | null;
	created_by: number;
	updated_by: number;
	freeze_assignee: boolean;
	user_manager: { id: number; name: string } | null;
	user_assignees: Array<{ id: number; name: string }>;
	staff_group_assignees: Array<{ id: number; name: string }>;
	task_documents: any[];
	custom_fields?: Record<string, any> | string | null;
	task_statuses?: IProjectTaskStatus[];
	applied_task_status?: { id: number; name: string, description: string, color_code:string};
    applied_project_task_status?: { id: number; name: string, description: string, color_code:string} | null,
    completed_status?: number,
    failed_status?: number;
}

export interface IProjectTaskFormData {
	user_manager: number;
	user_assignees: number[];
	staff_group_assignees: number[];
	documents?: string[];
	document_names?: string[];
	custom_fields?: Record<string, any> | string;
	task_name: string;
	project: number;
	deleted_at?: string | null;
	is_active: boolean;
	description: string;
	start_date?: string;
	end_date?: string;
	freeze_assignee: boolean;
	start_time?: string;
	end_time?: string;
	completion_date?: string
	created_by?: number;
	updated_by?: number;
	task_statuses?: IProjectTaskStatusFormData[];
    applied_project_task_status?: number,
    completed_status?: number,
    failed_status?: number;
	priority: number;

}


export interface IStandAloneTask extends IBaseApprovable {
	id: number;
	task_name: string;
	project: number;
	task_status: TaskStatusSummary;
	priority: TaskPrioritySummary | null;
	created_at: string;
	updated_at: string;
	deleted_at: string | null;
	is_active: boolean;
	description: string;
	start_date: string | null;
	end_date: string | null;
	completion_date: string | null;
	created_by: number;
	updated_by: number;
	freeze_assignee: boolean;
	user_manager: { id: number; name: string } | null;
	user_assignees: Array<{ id: number; name: string }>;
	staff_group_assignees: Array<{ id: number; name: string }>;
	task_documents: any[];
	custom_fields?: Record<string, any> | string | null;
	task_statuses?: ITaskStandAloneStatuses[];
	applied_task_status?: { id: number; name: string, description: string, color_code:string} | null;
    applied_project_task_status?: { id: number; name: string, description: string, color_code:string},
    completed_status?: { id: number; status_name: string; color_code: string; weight: number } | null; 
	failed_status?: { id: number; status_name: string; color_code: string; weight: number } | null; 
}


export interface IStandAloneTaskFormData {
	user_manager: number;
	user_assignees: number[];
	staff_group_assignees: number[];
	documents?: string[];
	document_names?: string[];
	custom_fields?: Record<string, any> | string;
	task_name: string;
	project?: number;
	priority: number;
	deleted_at?: string | null;
	is_active: boolean;
	description: string;
	start_date?: string;
	end_date?: string;
	freeze_assignee: boolean;
	start_time?: string;
	end_time?: string;
	completion_date?: string
	created_by?: number;
	updated_by?: number;
	task_statuses?: ITaskStandAloneStatusFormData [];
    applied_project_task_status?: number,
    completed_status?: number,
    failed_status?: number;

}



// export type IProjectStatus =
// 	| "not_started"
// 	| "in_progress"
// 	| "planning"
// 	| "on_hold"
// 	| "cancelled"
// 	| "completed";

// export interface IProject {
// 	id: number;
// 	institution: number;
// 	project_name: string;
// 	managers: IEmployee[];
// 	assignees: IEmployee[];
// 	description: string;
// 	start_date: string;
// 	end_date: string;
// 	project_status: IProjectStatus;
// 	project_tasks: IProjectTask[];
// }

// export interface IProjectFormData {
// 	institution: number;
// 	project_name: string;
// 	managers: number[];
// 	assignees: number[];
// 	description: string;
// 	start_date: string;
// 	end_date: string;
// 	project_status?: IProjectStatus;
// 	approver_groups: number[];
//     user_groups: number[];
// }

// Project approval status (from BaseApprovableModel)
export type ProjectApprovalStatus =
	| 'under_creation'
	| 'pending'
	| 'approved'
	| 'rejected';

export interface IProjectDocument {
	id: number;
	approvals: any[];
	name: string;
	created_at: string;
	updated_at: string;
	deleted_at: string | null;
	is_active: boolean;
	approval_status: string;
	document: string;
	created_by: number | null;
	updated_by: number | null;
	project: number;
}

export interface IProject {
	id: number;
	institution: number | null;
	project_name: string;
	description: string;
	milestones: Record<string, any>;
	start_date: string | null;
	end_date: string | null;
	project_status: IProjectStatus | null;
	completion_date: string | null;
	project_tasks: IProjectTask[];
	project_documents: IProjectDocument[];
	created_at: string;
	updated_at: string;
	approval_status: ApprovableEntityStatus;
	user_manager: { id: number; name: string } | null;
	user_assignees: Array<{ id: number; name: string }>;
	staff_group_assignees: Array<{ id: number; name: string }>;
	custom_fields?: ICustomField[] | null;
	project_task_statuses?: IProjectTaskStatuses[];
	completed_status?: { id: number; status_name: string, color_code:string, weight:number } | null;
  	failed_status?:  { id: number; status_name: string, color_code:string, weight:number } | null;

}

export interface IProjectFormData {
	user_manager: number;
	user_assignees: number[];
	staff_group_assignees: number[];
	documents?: string[];
	document_names?: string[];
	project_name: string;
	project_status: number;
	milestones?: string;
	institution: number;
	deleted_at?: string | null;
	is_active?: boolean;
	completion_date?: string | null;
	description: string;
	start_date: string | null;
	end_date: string | null;
	created_by?: number;
	updated_by?: number;
	custom_fields?: ICustomField[];
	project_task_statuses?: IProjectTaskStatusFormData[];
	completed_status?: number;
  	failed_status?: number;
}

export type IDurationUnit = "days" | "months" | "years";


export type CustomFieldType =
	| "text"
	| "date"
	| "select"
	| "checkbox"
	| "number"
	| "textarea"
	| "file";

export type IQuestionCategory = "interview" | "performance_review" | "360_feedback" | "general";

export type IQuestionType = "text" | "rating" | "multiple_choice" | "yes_no";

export interface CustomField {
	id: string;
	name: string;
	description: string;
	type: IQuestionType;
	value?: any;
	is_required?: boolean;
	options?: string[]; // For multiple_choice
}

export interface CustomFieldFormData {
	title: string;
	description: string;
	question_type: IQuestionType;
	options?: string[]; // For multiple_choice
}

export interface IQuestionTemplate {
	id: number;
	institution: IUserInstitution;
	name: string;
	description?: string | null;
	category: IQuestionCategory;
	questions: CustomField[];
}

export interface IQuestionTemplateFormData {
	institution: number;
	name: string;
	description?: string;
	category: IQuestionCategory;
	questions: CustomField[];
}

export type IApplicableFor = "managers" | "assignees";

export type IBonusFor = "completing" | "closing";

export type IConditionOperator = "=" | "<" | ">" | "<=" | ">=";

export type IEventMode = "physical" | "online" | "hybrid";


export interface IMeeting {
	id: number;
	institution: IUserInstitution;
	title: string;
	description?: string | null;
	start_time: string;
	end_time: string;
	mode: IEventMode;
	location?: string | null;
	online_link?: string | null;
	participants: IEmployee[];
	organizer?: IEmployee | null;
	agenda?: string | null;
	minutes?: string | null;
	is_recurring: boolean;
	recurrence_rule?: string | null;
	calendar_event_id?: string | null;
}

export interface IMeetingFormData {
	institution: number;
	title: string;
	description?: string;
	start_time: string;
	end_time: string;
	mode: IEventMode;
	location?: string;
	participant_ids: number[];
	organizer_id?: number;
	agenda?: string;
	minutes?: string;
	is_recurring?: boolean;
	recurrence_rule?: string;
	online_link?: string | null;
}

export interface IMeetingIntegrationFormData {
	is_active?: boolean;
	platform: "zoom" | "google_meet" | "microsoft_teams" | "other";
	api_key?: string;
	api_secret?: string;
	oauth_token?: string;
	oauth_refresh_token?: string;
	tenant_id?: string;
}

export interface IMeetingIntegration extends IBaseApprovable {
	id: number;
	is_active?: boolean;
	platform: "zoom" | "google_meet" | "microsoft_teams" | "other";
	api_key: string | null;
	api_secret: string | null;
	oauth_token: string | null;
	oauth_refresh_token: string | null;
	tenant_id: string | null;
	updated_at: string;
	institution: number;
}



export interface IEmailProviderConfigFormData {
	provider: "cpanel" | "google_workspace" | "microsoft_365";
	domain: string;
	webmail_url?: string;
	format_template?: string;
	quota?: number;
	port?: string;
	admin_email?: string;
	api_url?: string;
	api_username?: string;
	api_password?: string;
	api_client_id?: string;
	api_client_secret?: string;
	api_token?: string;
}

export interface IEmailProviderConfig {
	id: number;
	approval_status: "under_creation" | "pending_approval" | "approved" | "rejected";
	provider: "cpanel" | "google_workspace" | "microsoft_365";
	domain: string;
	webmail_url: string | null;
	format_template: string;
	quota: number;
	port: string;
	admin_email: string | null;
	api_url: string | null;
	api_username: string | null;
	api_password: string | null;
	api_client_id: string | null;
	api_client_secret: string | null;
	api_token: string | null;
	updated_at: string;
	institution: number;
}

// Apply approvals to existing READ interfaces via declaration merging
export interface IAllowanceType extends IBaseApprovable { }
export interface IAsset extends IBaseApprovable { }
export interface IAssetAllocation extends IBaseApprovable { }
export interface IAssetRequest extends IBaseApprovable { }
export interface IAssetReturn extends IBaseApprovable { }

export interface IBranchPenaltyConfig extends IBaseApprovable { }
export interface IBranchShift extends IBaseApprovable { }
export interface IBranchSpotCheckSetting extends IBaseApprovable { }
export interface IBranchWorkingDays extends IBaseApprovable { }

export interface ICalendar extends IBaseApprovable { }
export interface ICompany extends IBaseApprovable { }
export interface ICompanyBranch extends IBaseApprovable { }
export interface ICompanyDepartment extends IBaseApprovable { }
export interface ICompanyPosition extends IBaseApprovable { }

export interface IDeduction extends IBaseApprovable { }
export interface IDeductionType extends IBaseApprovable { }

export interface IEmployee extends IBaseApprovable { }
export interface IEmployeeAllowance extends IBaseApprovable { }
export interface IEmployeeContract extends IBaseApprovable { }
export interface IEmployeeDeduction extends IBaseApprovable { }
export interface IEmployeeDocument extends IBaseApprovable { }
export interface IEmployeeEmergencyContact extends IBaseApprovable { }
export interface IEmployeeLeave extends IBaseApprovable { }
export interface IEmployeeLeaveBalance extends IBaseApprovable { }
export interface IEmployeeOvertime extends IBaseApprovable { }
export interface IEmployeePenalty extends IBaseApprovable { }
export interface IEmployeeShift extends IBaseApprovable { }

export interface IHoliday extends IBaseApprovable { }

export interface ILeaveType extends IBaseApprovable { }
export interface ILoan extends IBaseApprovable { }
export interface ILoanType extends IBaseApprovable { }

export interface IOvertimeType extends IBaseApprovable { }

export interface IPayrollPeriod extends IBaseApprovable { }
export interface IPayrollPeriodEmployee extends IBaseApprovable { }
export interface IPenalty extends IBaseApprovable { }

export interface IRole extends IBaseApprovable { }

export interface IShift extends IBaseApprovable { }
export interface ISpotCheck extends IBaseApprovable { }

export interface ITimesheet extends IBaseApprovable { }
export interface ITimesheetEntry extends IBaseApprovable { }
export interface IJobPosition extends IBaseApprovable { }
export interface IDepartment extends IBaseApprovable { }
export interface JobPositionAdvert extends IBaseApprovable { }
export interface JobApplication extends IBaseApprovable { }
export interface ISeparationPolicy extends IBaseApprovable { }
export interface IProject extends IBaseApprovable { }
export interface IInterview extends IBaseApprovable { }
export interface ITermination extends IBaseApprovable { }
export interface IOnBoarding extends IBaseApprovable { }
export interface ITax extends IBaseApprovable { }
export interface IProjectTask extends IBaseApprovable { }

export interface IPeriod extends IBaseApprovable { }
export interface IObjective extends IBaseApprovable { }
export interface IEmployeeObjective extends IBaseApprovable { }
export interface IKeyResult extends IBaseApprovable { }
export interface IFeedback360 extends IBaseApprovable { }
export interface IEmployeeBonusPoint extends IBaseApprovable { }
export interface IQuestionTemplate extends IBaseApprovable { }
export interface IBonusPointSettings extends IBaseApprovable { }
export interface IMeeting extends IBaseApprovable { }
