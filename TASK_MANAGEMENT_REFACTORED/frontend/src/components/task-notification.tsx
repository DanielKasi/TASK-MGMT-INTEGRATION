// "use client";

// import type React from "react";

// import {useState, useEffect} from "react";
// import {Bell} from "lucide-react";
// import {useRouter} from "next/navigation";
// import {formatDistanceToNow} from "date-fns";
// import {useSelector} from "react-redux";
// import {Icon} from "@iconify/react";

// import {Button} from "@/platform/v1/components";
// import {
//   DropdownMenu,
//   DropdownMenuContent,
//   DropdownMenuGroup,
//   DropdownMenuItem,
//   DropdownMenuLabel,
//   DropdownMenuSeparator,
//   DropdownMenuTrigger,
// } from "@/platform/v1/components";
// import {Badge} from "@/platform/v1/components";
// import {selectUser} from "@/store/auth/selectors-context-aware";
// import { ApprovalTask } from "@/types/approvals.types";

// export function TaskNotification() {
//   const [tasks, setTasks] = useState<ApprovalTask[]>([]);
//   const router = useModuleNavigation();
//   const currentUser = useSelector(selectUser);
//   const {tasks: apiTasks, connected} = useWebSocket();

//   // Convert API tasks to display format
//   useEffect(() => {
//     if (!apiTasks || !apiTasks.length) return;

//     // Filter only pending tasks
//     const pendingTasks = apiTasks.filter(
//       (task) =>
//         ["pending"].some((status) => status === task.status) &&
//         (task.step.roles_details.find((role: {id: number}) =>
//           currentUser?.roles.some((u_role) => u_role.id === role.id),
//         ) ||
//           task.step.approvers_details?.map(
//             (appr: {approver_user: {user: {id: number | undefined}}}) =>
//               appr.approver_user.user.id === currentUser?.id,
//           )),
//     );

//     // Convert API tasks to display format
//     const convertedTasks = pendingTasks.map((task) => {
//       // Determine task type based on action category
//       let taskType:
//         | "product_approval"
//         | "purchase_order_approval"
//         | "stock_movement_to_branch"
//         | "stock_movement_to_shelf"
//         | "return_request"
//         | "other" = "other";

//       if (task.step.action_details.code.toLowerCase().includes("product")) {
//         taskType = "product_approval";
//       } else if (task.step.action_details.code.toLowerCase().includes("purchase")) {
//         taskType = "purchase_order_approval";
//       } else if (task.step.action_details.code.toLowerCase().includes("branch")) {
//         taskType = "stock_movement_to_branch";
//       } else if (task.step.action_details.code.toLowerCase().includes("shelf")) {
//         taskType = "stock_movement_to_shelf";
//       } else if (task.step.action_details.code.toLowerCase().includes("return")) {
//         taskType = "return_request";
//       }

//       // Build link based on action type
//       let link = "#";

//       if (taskType === "product_approval") {
//         link = `/inventory/products/${task.object_id}`;
//       } else if (taskType === "purchase_order_approval") {
//         link = `/inventory/purchase-orders/${task.object_id}`;
//       } else if (taskType === "stock_movement_to_branch") {
//         link = `/main-branch-allocations/${task.object_id}`;
//       } else if (taskType === "stock_movement_to_shelf") {
//         link = `/main-branch-allocations/${task.object_id}`;
//       } else if (taskType === "return_request") {
//         link = `/return_requests/${task.object_id}`;
//       }

//       return {
//         id: task.id,
//         title: task.step.step_name,
//         description: `Approval Needed`,
//         time: formatDistanceToNow(new Date(task.updated_at), {
//           addSuffix: true,
//         }),
//         link,
//         type: taskType,
//         objectId: task.object_id,
//       };
//     });

//     setTasks(convertedTasks as any);
//   }, [apiTasks, currentUser, connected]);

//   const handleTaskClick = (link: string) => {
//     router.push(link);
//   };

//   const viewAllTasks = () => {
//     router.push("/tasks");
//   };

//   return (
//     <DropdownMenu>
//       <DropdownMenuTrigger asChild>
//         <button className=" text-gray-900 rounded-full bg-white hover:bg-gray-100 p-3 border-none outline-none relative">
//           <Icon icon="hugeicons:notification-02" width="24" height="24" />
//           {tasks.length > 0 && (
//             <div className="absolute top-0 right-0 w-2 h-2 bg-sidebar-selected rounded-full" />
//           )}
//         </button>
//       </DropdownMenuTrigger>
//       <DropdownMenuContent align="end" className="w-80 rounded-xl">
//         <DropdownMenuLabel className="flex justify-between items-center">
//           <span>Approval Tasks</span>
//           {tasks.length > 0 && <Badge variant="outline">{tasks.length}</Badge>}
//         </DropdownMenuLabel>
//         <DropdownMenuSeparator />
//         <div className="max-h-[300px] overflow-y-auto">
//           {tasks.length > 0 ? (
//             <DropdownMenuGroup>
//               {tasks.slice(0, 2).map((task) => (
//                 <DropdownMenuItem key={task.id} className="cursor-pointer p-0">
//                   <div role="task-clik-handler"
//                     className="flex flex-col w-full p-3 hover:bg-accent rounded-md"
//                     onClick={() => handleTaskClick(task.link)}
//                   >
//                     <div className="flex justify-between items-start">
//                       <span className="font-medium">{task.title}</span>
//                       <span className="text-xs text-muted-foreground">{task.time}</span>
//                     </div>
//                     <p className="text-sm text-muted-foreground mt-1">{task.description}</p>
//                     <div className="flex justify-between items-center mt-2">
//                       <Badge
//                         className="text-xs"
//                         variant={
//                           task.type === "product_approval"
//                             ? "destructive"
//                             : task.type === "purchase_order_approval"
//                               ? "success"
//                               : task.type === "return_request"
//                                 ? "info"
//                                 : task.type === "stock_movement_to_shelf"
//                                   ? "warning"
//                                   : task.type === "stock_movement_to_branch"
//                                     ? "default"
//                                     : "outline"
//                         }
//                       >
//                         {task.type === "product_approval"
//                           ? "Product"
//                           : task.type === "purchase_order_approval"
//                             ? "Purchase Order"
//                             : task.type === "stock_movement_to_branch"
//                               ? "Stock Allocation To Branch"
//                               : task.type === "stock_movement_to_shelf"
//                                 ? "Stock Allocation To Shelf"
//                                 : task.type === "return_request"
//                                   ? "Return Request"
//                                   : "UnKnown"}
//                       </Badge>
//                     </div>
//                   </div>
//                 </DropdownMenuItem>
//               ))}
//             </DropdownMenuGroup>
//           ) : (
//             <div className="py-4 text-center text-sm text-muted-foreground">
//               No pending approvals
//             </div>
//           )}
//         </div>
//         <>
//           <DropdownMenuSeparator />
//           <div className="p-2">
//             <Button className="w-full" size="sm" variant="outline" onClick={viewAllTasks}>
//               View All Tasks ({tasks.length})
//             </Button>
//           </div>
//         </>
//       </DropdownMenuContent>
//     </DropdownMenu>
//   );
// }
