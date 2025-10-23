"use client";

import type { UserProfile } from "@/types/user.types";
import { useEffect, useState } from "react";
import {
  ChevronDown,
  Eye,
  Trash2,
  MoreVertical,
  Edit,
  ArrowLeft,
} from "lucide-react";
import { useModuleNavigation } from "@/hooks/use-module-navigation";
import { Icon } from "@iconify/react";
import { AddUserForm } from "./addUser";
import { EditUserForm } from "./edit-user";
import { ConfirmationDialog } from "@/components/confirmation-dialog";
import { Button } from "@/platform/v1/components";
import { Input } from "@/platform/v1/components";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/platform/v1/components";
import { Avatar, AvatarFallback } from "@/platform/v1/components";
import { capitalizeEachWord, getDefaultInstitutionId } from "@/lib/helpers";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/platform/v1/components";
import {ProtectedComponent} from "@/platform/v1/components";
import { PERMISSION_CODES } from "@/constants";
import { PaginatedTable } from "@/components/PaginatedTable";
import { PROFILES_API } from "@/lib/utils";
import { TableSkeleton } from "@/components/common/table-skeleton";
import apiRequest from "@/lib/apiRequest";
import { toast } from "sonner";
import { PaginatedTableWrapper } from "@/components/common/tables/paginated-table-wrapper";

export default function StaffPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedBranch, setSelectedBranch] = useState("All Branches");
  const [selectedRole, setSelectedRole] = useState("All Roles");
  const [selectedStatus, setSelectedStatus] = useState("All status");
  const [allUserProfiles, setAllUserProfiles] = useState<UserProfile[]>([]);
  const router = useModuleNavigation();
  const [userToDelete, setUserToDelete] = useState<UserProfile | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [selectedUserForEdit, setSelectedUserForEdit] =
    useState<UserProfile | null>(null);

  const getUserRoleName = (userProfile: UserProfile) => {
    if (userProfile.user.roles && userProfile.user.roles.length > 0) {
      return capitalizeEachWord(userProfile.user.roles[0].name);
    }

    return "No Role Assigned";
  };

  return (
    <div className="space-y-6 overflow-x-hidden">
      {/* Header and Filters */}
      <div className="bg-white rounded-lg border shadow-sm min-h-screen overflow-hidden">
        <div className="p-4 sm:p-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                className="rounded-full aspect-square"
                onClick={() => router.push("/admin")}
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight">
                Staff
              </h1>
            </div>
          </div>
        </div>
        <div className="p-4 sm:p-6 overflow-x-hidden">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-4 justify-between w-full sm:w-auto">
              <div className="relative flex-1 sm:max-w-sm">
                <Icon
                  icon="hugeicons:search-01"
                  className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 !h-5 !w-5"
                />
                <Input
                  placeholder="Search Staff"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 w-full"
                />
              </div>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    className="flex-1 min-w-[90px] sm:w-[130px] border-none bg-transparent focus:outline-none focus:ring-0 shadow-none text-xs sm:text-sm px-1 sm:px-3"
                    variant="outline"
                  >
                    <span className="truncate">{selectedBranch}</span>
                    <ChevronDown className="ml-1 h-3 w-3 sm:h-4 sm:w-4 flex-shrink-0" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem
                    onClick={() => setSelectedBranch("All Branches")}
                  >
                    All Branches
                  </DropdownMenuItem>
                  {Array.from(
                    new Set(
                      allUserProfiles.flatMap(
                        (profile) =>
                          profile.user.branches?.map(
                            (branch) => branch.branch_name
                          ) || []
                      )
                    )
                  ).map((branch) => (
                    <DropdownMenuItem
                      key={branch}
                      onClick={() => setSelectedBranch(branch)}
                    >
                      {branch}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    className="flex-1 min-w-[90px] sm:w-[130px] border-none bg-transparent focus:outline-none focus:ring-0 shadow-none text-xs sm:text-sm"
                    variant="outline"
                  >
                    <span className="truncate">{selectedRole}</span>
                    <ChevronDown className="ml-1 h-3 w-3 sm:h-4 sm:w-4 flex-shrink-0" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem
                    onClick={() => setSelectedRole("All Roles")}
                  >
                    All Roles
                  </DropdownMenuItem>
                  {Array.from(
                    new Set(
                      allUserProfiles
                        .filter(
                          (profile) =>
                            profile.user.roles && profile.user.roles.length > 0
                        )
                        .map((profile) =>
                          capitalizeEachWord(profile.user.roles[0].name)
                        )
                    )
                  ).map((role) => (
                    <DropdownMenuItem
                      key={role}
                      onClick={() => setSelectedRole(role)}
                    >
                      {role}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    className="flex-1 min-w-[90px] sm:w-[130px] border-none bg-transparent focus:outline-none focus:ring-0 shadow-none text-xs sm:text-sm"
                    variant="outline"
                  >
                    <span className="truncate">{selectedStatus}</span>
                    <ChevronDown className="ml-1 h-3 w-3 sm:h-4 sm:w-4 flex-shrink-0" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem
                    onClick={() => setSelectedStatus("All status")}
                  >
                    All status
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setSelectedStatus("Active")}>
                    Active
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => setSelectedStatus("Inactive")}
                  >
                    Inactive
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <ProtectedComponent
                permissionCode={PERMISSION_CODES.CAN_CREATE_USERS}
              >
                <AddUserForm onAddSuccess={() => window.location.reload()} />
              </ProtectedComponent>
            </div>
          </div>
        </div>
        <div className="p-4 sm:p-6 overflow-x-hidden">
          <PaginatedTableWrapper<UserProfile>
            fetchFirstPage={async () => {
              const institutionId = getDefaultInstitutionId();

              if (!institutionId) {
                throw new Error("Institution ID is required");
              }

              return await PROFILES_API.getPaginatedUserProfiles({
                page: 1,
                search: searchQuery || undefined,
              });
            }}
            fetchFromUrl={({ url }) =>
              PROFILES_API.getPaginatedUserProfilesFromUrl({ url })
            }
            deps={[searchQuery]}
            className=""
            footerClassName="pt-4"
          >
            {({ data: userData, loading: userLoading, refresh }) => {
              useEffect(() => {
                if (userData?.results) {
                  setAllUserProfiles(userData.results);
                }
              }, [userData?.results]);

              if (userLoading) {
                return <TableSkeleton rows={10} columns={6} />;
              }

              if (!userData?.results || userData.results.length === 0) {
                return (
                  <div className="text-center py-8 text-gray-500">
                    {searchQuery
                      ? "No users found matching your search criteria"
                      : "No users found"}
                  </div>
                );
              }

              // Apply client-side filters
              const filteredStaff = userData.results.filter((userProfile) => {
                // Branch filter
                const matchesBranch =
                  selectedBranch === "All Branches" ||
                  userProfile.user.branches?.some(
                    (branch) => branch.branch_name === selectedBranch
                  );

                // Role filter
                const matchesRole =
                  selectedRole === "All Roles" ||
                  (userProfile.user.roles &&
                    userProfile.user.roles.length > 0 &&
                    capitalizeEachWord(userProfile.user.roles[0].name) ===
                      selectedRole);

                // Status filter
                const matchesStatus =
                  selectedStatus === "All status" ||
                  (selectedStatus === "Active" && userProfile.user.is_active) ||
                  (selectedStatus === "Inactive" &&
                    !userProfile.user.is_active);

                return matchesBranch && matchesRole && matchesStatus;
              });

              const handleDeleteUser = async () => {
                if (!userToDelete) return;

                try {
                  setIsDeleting(true);
                  await apiRequest.delete(`user/${userToDelete.user.id}/`);
                  toast.success("User deleted successfully");
                  refresh();
                } catch (error: any) {
                  toast.error(error.message || "Failed to delete user");
                } finally {
                  setUserToDelete(null);
                  setIsDeleting(false);
                }
              };

              if (filteredStaff.length === 0) {
                return (
                  <div className="text-center py-8 text-gray-500">
                    No users found matching the selected filters.
                  </div>
                );
              }

              return (
                <>
                  {/* Desktop Table */}
                  <div className="hidden sm:block rounded-md overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Name</TableHead>
                          <TableHead>Contact Info</TableHead>
                          <TableHead>Role</TableHead>
                          <TableHead>Branch Access</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead className="w-12">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredStaff.map((userProfile) => (
                          <TableRow key={userProfile.id}>
                            <TableCell>
                              <div className="flex items-center gap-3">
                                <Avatar className="h-8 w-8 bg-gray-200">
                                  <AvatarFallback className="text-gray-600">
                                    {userProfile.user.fullname
                                      ?.substring(0, 2)
                                      .toUpperCase() || "??"}
                                  </AvatarFallback>
                                </Avatar>
                                <div className="font-medium">
                                  {userProfile.user.fullname
                                    ? capitalizeEachWord(
                                        userProfile.user.fullname
                                      )
                                    : "Unknown User"}
                                </div>
                              </div>
                            </TableCell>
                            <TableCell className="text-gray-600">
                              {userProfile.user.email}
                            </TableCell>
                            <TableCell className="text-gray-600">
                              {getUserRoleName(userProfile)}
                            </TableCell>
                            <TableCell className="text-gray-600">
                              {userProfile.user.branches?.length
                                ? userProfile.user.branches
                                    .map((branch) => branch.branch_name)
                                    .join(", ")
                                : "No branches assigned"}
                            </TableCell>
                            <TableCell>
                              <span
                                className={`px-2 py-1 text-xs rounded-full ${
                                  userProfile.user.is_active
                                    ? "bg-[#dcfce7] text-[#10b981]"
                                    : "bg-[#fee2e2] text-[#ef4444]"
                                }`}
                              >
                                {userProfile.user.is_active
                                  ? "Active"
                                  : "Inactive"}
                              </span>
                            </TableCell>
                            <TableCell>
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="sm">
                                    <Icon
                                      icon="hugeicons:more-horizontal-square-01"
                                      className="!h-4 !w-4 text-dark"
                                    />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuItem
                                    onClick={() =>
                                      router.push(
                                        `/users/${userProfile.user.id}`
                                      )
                                    }
                                  >
                                    <Eye className="h-4 w-4 mr-2" />
                                    View Details
                                  </DropdownMenuItem>
                                  <DropdownMenuItem
                                    onClick={() => {
                                      setSelectedUserForEdit(userProfile);
                                      setIsEditDialogOpen(true);
                                    }}
                                  >
                                    <Edit className="h-4 w-4 mr-2" />
                                    Edit
                                  </DropdownMenuItem>
                                  <DropdownMenuItem
                                    className="text-red-600"
                                    onClick={() => setUserToDelete(userProfile)}
                                  >
                                    <Trash2 className="h-4 w-4 mr-2" />
                                    Delete
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>

                  {/* Mobile Cards */}
                  <div className="sm:hidden space-y-3 overflow-x-hidden">
                    {filteredStaff.map((userProfile) => (
                      <div
                        key={userProfile.id}
                        className="bg-gray-50 rounded-lg p-4 border overflow-hidden"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              <Avatar className="h-6 w-6 bg-gray-200 flex-shrink-0">
                                <AvatarFallback className="text-gray-600 text-xs">
                                  {userProfile.user.fullname
                                    ?.substring(0, 2)
                                    .toUpperCase() || "??"}
                                </AvatarFallback>
                              </Avatar>
                              <h3 className="font-semibold text-gray-900 truncate">
                                {userProfile.user.fullname
                                  ? capitalizeEachWord(
                                      userProfile.user.fullname
                                    )
                                  : "Unknown User"}
                              </h3>
                            </div>
                            <div className="space-y-1 mb-2">
                              <p className="text-sm text-gray-600 truncate break-words">
                                {userProfile.user.email}
                              </p>
                              <p className="text-sm text-gray-600 break-words">
                                Role: {getUserRoleName(userProfile)}
                              </p>
                              <p className="text-sm text-gray-600 break-words">
                                Branches:{" "}
                                {userProfile.user.branches?.length
                                  ? userProfile.user.branches
                                      .map((branch) => branch.branch_name)
                                      .join(", ")
                                  : "No branches assigned"}
                              </p>
                              <div className="flex items-center gap-2">
                                <span
                                  className={`px-2 py-1 text-xs rounded-full ${
                                    userProfile.user.is_active
                                      ? "bg-[#dcfce7] text-[#10b981]"
                                      : "bg-[#fee2e2] text-[#ef4444]"
                                  }`}
                                >
                                  {userProfile.user.is_active
                                    ? "Active"
                                    : "Inactive"}
                                </span>
                              </div>
                            </div>
                          </div>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="flex-shrink-0"
                              >
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem
                                onClick={() =>
                                  router.push(`/users/${userProfile.user.id}`)
                                }
                              >
                                <Eye className="h-4 w-4 mr-2" />
                                View Details
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => {
                                  setSelectedUserForEdit(userProfile);
                                  setIsEditDialogOpen(true);
                                }}
                              >
                                <Edit className="h-4 w-4 mr-2" />
                                Edit
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                className="text-red-600"
                                onClick={() => setUserToDelete(userProfile)}
                              >
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </div>
                    ))}
                  </div>
                  {selectedUserForEdit && (
                    <EditUserForm
                      user={selectedUserForEdit}
                      open={isEditDialogOpen}
                      onOpenChange={setIsEditDialogOpen}
                      onEditSuccess={() => {
                        refresh();
                        setIsEditDialogOpen(false);
                        setSelectedUserForEdit(null);
                      }}
                    />
                  )}
                  {userToDelete && (
                    <ConfirmationDialog
                      isOpen={!!userToDelete}
                      title={`Delete ${userToDelete.user.fullname}`}
                      description="Are you sure you want to delete this user? This action cannot be undone and will remove all associated data."
                      onConfirm={handleDeleteUser}
                      onClose={() => setUserToDelete(null)}
                      disabled={isDeleting}
                    />
                  )}
                </>
              );
            }}
          </PaginatedTableWrapper>
        </div>
      </div>
    </div>
  );
}
